# Домашняя работа 3. SSH-доступ к GitHub

**Швецов Леонид Сергеевич**

Репозиторий: https://github.com/lshvetsov/netology

## 1. SSH-клиент и ключ

Проверил SSH-клиент на macOS:

```bash
ssh -V
```

SSH уже установлен, версия — `OpenSSH_9.9p2`. Создал новую пару ключей Ed25519:

```bash
ssh-keygen -t ed25519 -C "netology-hw3" -f ~/.ssh/id_ed25519_netology_hw3
```

При создании защитил приватный ключ парольной фразой.
Публичный ключ сохранил в `~/.ssh/`. Затем добавил ключ в ssh-agent,
чтобы не вводить парольную фразу при каждом подключении.

[Вывод проверки клиента и ключа](evidence/01-client-and-key.txt).

## 2. Добавление ключа в GitHub

Скопировал содержимое файла с расширением `.pub`. В GitHub открыл
**Settings → SSH and GPG keys → New SSH key**, вставил ключ и сохранил
с названием `Netology HW3 SSH`. Тип ключа — `Authentication Key`.

[Подтверждение добавления](evidence/02-github-key.txt).

## 3. Проверка SSH-подключения

Проверил подключение:

```bash
ssh -T git@github.com
```

GitHub ответил:

```text
Hi lshvetsov! You've successfully authenticated, but GitHub does not provide shell access.
```

GitHub подтвердил вход по ключу. Пароль не запрашивался.

[Полный вывод проверки](evidence/03-ssh-connection.txt).

## 4. Клонирование и отправка изменений

Клонировал свой репозиторий по SSH-адресу:

```bash
git clone git@github.com:lshvetsov/netology.git netology-ssh
cd netology-ssh
```

Добавил в клонированный репозиторий папку с этой работой, создал коммит и отправил
изменения:

```bash
git add program-engineering/HW3-SSH
git commit -m "Программная инженерия: SSH-доступ к GitHub"
git push origin main
```

Клонирование и отправка изменений прошли без запроса пароля.

[Вывод клонирования](evidence/04-clone.txt) ·
[Вывод commit и push](evidence/05-commit-and-push.txt).
