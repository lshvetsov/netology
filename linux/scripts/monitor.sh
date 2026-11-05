#!/bin/bash
set -eu
export LC_ALL=C

if [[ $EUID -ne 0 || ! -f /etc/linux-oom-lab ]]; then
    echo 'Запустите через sudo внутри учебной VM' >&2
    exit 1
fi

report=/var/log/linux-oom-lab/report.txt
mkdir -p /var/log/linux-oom-lab
read -r total available < <(awk '
    /MemTotal:/ {total=$2} /MemAvailable:/ {available=$2}
    END {print total, available}' /proc/meminfo)
read -r swap_total swap_free < <(awk '
    /SwapTotal:/ {total=$2} /SwapFree:/ {free=$2}
    END {print total, free}' /proc/meminfo)
memory_percent=$((100 * available / total))
swap_percent=0
if (( swap_total > 0 )); then
    swap_percent=$((100 * (swap_total - swap_free) / swap_total))
fi
cpu=$(vmstat 1 2 | tail -n 1 | awk '{print $13+$14}')

# Берём два интервала проверки, чтобы не потерять событие на границе.
if ! events=$(journalctl -b -p 0..3 --since '10 minutes ago' \
    --no-pager --quiet -o short-iso 2>&1); then
    echo "Ошибка чтения журнала: $events" >&2
    exit 1
fi
if ! kernel=$(journalctl -k -b --since '10 minutes ago' \
    --no-pager --quiet -o short-iso 2>&1); then
    echo "Ошибка чтения журнала ядра: $kernel" >&2
    exit 1
fi
oom=$(printf '%s\n' "$kernel" | \
    grep -Ei 'invoked oom-killer|oom-kill:|out of memory|killed process' || true)

{
    echo "===== $(date --iso-8601=seconds) ====="
    echo 'ПАМЯТЬ И SWAP (МиБ)'
    free -m
    echo "Доступно RAM: $memory_percent%; занято swap: $swap_percent%"
    echo "CPU (us + sy за 1 секунду): $cpu%"
    uptime
    echo 'ПРОЦЕССЫ С НАИБОЛЬШИМ RSS (КиБ)'
    ps -eo pid,comm,rss,%cpu --sort=-rss | head -n 6
    echo 'ДИАГНОСТИКА'
    if (( memory_percent < 10 )); then echo 'ВНИМАНИЕ: доступно менее 10% RAM';
    else echo 'RAM: запас более 10% или равен 10%'; fi
    if (( swap_percent >= 90 )); then echo 'ВНИМАНИЕ: swap заполнен на 90% или больше';
    else echo 'Swap: заполнение менее 90%'; fi
    if (( cpu >= 85 )); then echo 'ВНИМАНИЕ: CPU занят на 85% или больше';
    else echo 'CPU: загрузка менее 85%'; fi
    echo 'ОШИБКИ И КРИТИЧЕСКИЕ СОБЫТИЯ (уровни 0-3, за 10 минут)'
    echo "${events:-Не обнаружены}"
    echo 'OOM В ЖУРНАЛЕ ЯДРА (за 10 минут)'
    echo "${oom:-Не обнаружен}"
    echo
} >> "$report"
