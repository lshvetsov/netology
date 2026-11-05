# Итоговая работа по Linux

**Швецов Леонид Сергеевич**

Тема: поведение Linux при нехватке памяти.

Для работы использовал Ubuntu 24.04 в Lima: 2 CPU, 1 ГиБ RAM и swap 512 МиБ.
Скрипт постепенно занимал память, а проверка через cron записывала состояние системы
раз в пять минут. Примерно через 13 минут OOM-killer завершил процесс с утечкой.

[Работа в PDF](Швецов_Леонид_Сергеевич_Linux_Итоговая_работа.pdf) ·
[Версия DOCX](Швецов_Леонид_Сергеевич_Linux_Итоговая_работа.docx)

## Что лежит в папке

- `scripts/leak.py` — каждые пять секунд выделяет 8 МиБ и сохраняет блоки в списке.
- `scripts/monitor.sh` — проверяет RAM, CPU, swap и журнал, затем дописывает отчёт.
- `config/linux-oom-monitor.cron` — запускает монитор раз в пять минут.
- `evidence/` — результаты, журналы и скриншоты. Файлы пронумерованы по порядку просмотра.

## Подготовка

Для повторения нужна виртуальная машина с Ubuntu. Установить программы и создать
пользователя для процесса с утечкой:

```bash
sudo apt-get update
sudo apt-get install -y python3 cron procps
sudo touch /etc/linux-oom-lab
sudo useradd --system --no-create-home --shell /usr/sbin/nologin oomlab
```

Если подкачки ещё нет, создать swap-файл:

```bash
sudo dd if=/dev/zero of=/swapfile bs=1M count=512
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -m
```

В `linux-oom-lab` эта подготовка уже выполнена.

## Установка

Из папки проекта скопировать файлы в Lima и подключиться:

```bash
limactl start linux-oom-lab
limactl copy scripts/leak.py scripts/monitor.sh config/linux-oom-monitor.cron linux-oom-lab:/tmp/
limactl shell linux-oom-lab
```

Установить скрипты и расписание:

```bash
sudo mkdir -p /opt/linux-oom-lab /var/log/linux-oom-lab
sudo install -m 755 /tmp/leak.py /tmp/monitor.sh /opt/linux-oom-lab/
sudo install -m 644 /tmp/linux-oom-monitor.cron /etc/cron.d/linux-oom-monitor
sudo systemctl enable --now cron
bash -n /opt/linux-oom-lab/monitor.sh
```

## Запуск

Сначала сохранить состояние без нагрузки, затем запустить процесс:

```bash
sudo /opt/linux-oom-lab/monitor.sh
sudo systemd-run --unit=linux-oom-student --uid=oomlab \
  -p OOMScoreAdjust=700 -p RuntimeMaxSec=30min \
  /usr/bin/python3 -u /opt/linux-oom-lab/leak.py
```

`OOMScoreAdjust` повышает вероятность выбора имитатора при нехватке памяти.
Ограничение времени остановит процесс через 30 минут, если OOM не произойдёт.

Посмотреть текущее состояние:

```bash
free -m
ps -C python3 -o pid,comm,rss,%cpu
sudo tail -n 35 /var/log/linux-oom-lab/report.txt
```

После завершения проверить журнал и причину остановки:

```bash
sudo journalctl -k -b --no-pager | grep -Ei 'oom|killed process'
sudo systemctl show linux-oom-student -p Result -p ExecMainStatus
sudo /opt/linux-oom-lab/monitor.sh
```

Остановить процесс вручную: `sudo systemctl stop linux-oom-student`.
Перед повторным запуском с тем же именем после OOM:
`sudo systemctl reset-failed linux-oom-student`.

## Отчёт

Отчёт дописывается в `/var/log/linux-oom-lab/report.txt`.
Ошибки запуска из cron попадают в `/var/log/linux-oom-lab/cron.log`.

В отчёте есть объём доступной RAM, заполнение swap, загрузка CPU за одну секунду,
load average и процессы с наибольшим RSS. Предупреждения появляются, если доступно
меньше 10% RAM, занято не меньше 90% swap или CPU загружен на 85% и выше.
Из журнала выбираются ошибки уровней 0–3 и записи ядра об OOM за последние 10 минут.

В проведённом опыте доступная RAM уменьшилась с 750 до 91 МиБ, а в подкачке было занято 476 МиБ.
После завершения процесса стало доступно 773 МиБ RAM, использование swap снизилось
до 32 МиБ. Результаты и порядок просмотра файлов — в [evidence/README.md](evidence/README.md).
