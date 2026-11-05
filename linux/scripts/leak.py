#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess
import time

# Запускать только в подготовленной виртуальной машине.
if not Path('/etc/linux-oom-lab').exists():
    raise SystemExit('Нужна учебная VM linux-oom-lab')
subprocess.run(['systemd-detect-virt', '--vm'], check=True)

blocks = []
print(f'PID={os.getpid()}', flush=True)
while True:
    block = bytearray(8 * 1024 * 1024)
    # Записываем данные в каждую страницу памяти.
    for i in range(0, len(block), 4096):
        block[i] = 1
    blocks.append(block)
    print(f'Выделено {len(blocks) * 8} МиБ', flush=True)
    time.sleep(5)
