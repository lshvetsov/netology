# Домашняя работа 1. Работа с CI/CD

**Швецов Леонид Сергеевич**

Для всех десяти кейсов я взял один пример: HTTP-сервис, который переводит градусы Цельсия в градусы Фаренгейта. У него есть отдельный адрес `/health`, чтобы после развёртывания можно было проверить, что сервер отвечает. Само приложение работает на стандартной библиотеке Python.

## Локальный запуск

Команды ниже выполняются из папки `software-development/HW1`. В CI используется Python 3.12.

```bash
python3 -m unittest discover -s tests -v
mkdir -p dist
python3 -m zipapp src/ci_demo -o dist/ci-demo.pyz
PORT=8000 python3 dist/ci-demo.pyz
```

В другом терминале:

```bash
curl -fsS http://localhost:8000/health
curl -fsS 'http://localhost:8000/fahrenheit?celsius=20'
```

Ожидаемые ответы: `{"status": "ok"}` и `{"fahrenheit": 68.0}`. Для неверного значения сервис возвращает HTTP 400, для неизвестного адреса — HTTP 404. Сборка через `zipapp` упаковывает код в один запускаемый файл `ci-demo.pyz`.

## 1, 6 и 9. Сборка, уведомление и анализ кода в GitHub Actions

В [ci-cd-practice.yml](../../.github/workflows/ci-cd-practice.yml) три задачи. GitHub запускает их при пуше в ветку.

- `build` запускает тесты, собирает `ci-demo.pyz` и сохраняет его в **Artifacts**.
- `quality` запускает Ruff для проверки кода и Bandit для поиска распространённых проблем безопасности в Python. Bandit сканирует `src`. Для привязки HTTP-сервера к `0.0.0.0` сделано исключение только на одной строке, чтобы приложение было доступно извне контейнера.
- `notify` ждёт обе задачи и получает их статусы даже при ошибке. Успех означает, что прошли обе задачи. В Slack приходит статус и ссылка на прогон.

Для уведомлений нужен Incoming Webhook в тестовом канале Slack. Его URL добавляется в **Settings → Secrets and variables → Actions** под именем `SLACK_WEBHOOK_URL`. При отсутствии секрета задача пишет об этом в лог и пропускает отправку. Для проверки обоих исходов можно сделать два отдельных пуша в учебную ветку. Сначала с успешным тестом, затем с временно изменённым ожидаемым значением в тесте. После проверки восстановить тест отдельным коммитом.

Ruff и Bandit можно запустить вручную в виртуальном окружении:

```bash
python3 -m pip install -r requirements-ci.txt
ruff check src tests
bandit -r src
```

## 2 и 8. Тесты в GitLab CI/CD и развёртывание через Helm

Нужно создать проект в GitLab и отправить туда тот же Git-репозиторий. Корневой [.gitlab-ci.yml](../../.gitlab-ci.yml) подключает [конфигурацию ДЗ](.gitlab-ci.yml). `unit-tests` запускается при пуше в любую ветку. В ветке по умолчанию после тестов запускаются ещё две задачи:

1. `build-image` собирает Docker-образ через BuildKit и отправляет его в GitLab Container Registry с тегом полного SHA коммита.
2. `deploy-kubernetes` передаёт этот тег в Helm. Chart создаёт Deployment с проверкой готовности по `/health` и Service внутри кластера. Helm ждёт готовности и откатывает неудачное обновление благодаря `--atomic`.

Для развёртывания нужны включённый Container Registry, runner с поддержкой rootless BuildKit и кластер, до API которого может достучаться runner. В GitLab добавляется CI/CD-переменная типа **File** с именем `KUBE_CONFIG`. В ней должен быть kubeconfig с правами на ресурсы учебного namespace `ci-demo`. В самом namespace заранее создаётся секрет `gitlab-registry` с токеном чтения Container Registry. Одноимённый секрет используется при скачивании образа.

Проверка после прогона:

```bash
kubectl -n ci-demo rollout status deployment/ci-demo
kubectl -n ci-demo get deployment,pods,svc
kubectl -n ci-demo port-forward svc/ci-demo 8082:80
```

В другом терминале `curl -fsS http://localhost:8082/health` должен вернуть `{"status": "ok"}`.

## 3. CircleCI и Heroku

[CircleCI](circleci.yml) запускает задачу только для `main`. Внутри задачи проходят тесты, собирается Docker-образ для `linux/amd64`, образ отправляется в Heroku Container Registry и выпускается как процесс `web`. Последняя команда проверяет `/health` по адресу приложения.

Подключите репозиторий через интеграцию **GitHub App**. В настройках пайплайна CircleCI укажите **Config File Path** `software-development/HW1/circleci.yml` и включите триггер на пуши. Для развёртывания нужно приложение Heroku на стеке `container`. В настройки проекта CircleCI добавляются `HEROKU_APP_NAME`, `HEROKU_APP_URL`, `HEROKU_EMAIL` и `HEROKU_API_KEY`. Значение `HEROKU_APP_URL` берётся из карточки Heroku, например `https://имя-приложения.herokuapp.com` со своим доменом. Heroku должен запустить один web dyno, чтобы можно было проверить HTTP-ответ.

## 4, 5 и 10. Docker, Jenkins и миграции

[Dockerfile](Dockerfile) собирает тот же `ci-demo.pyz` внутри образа Python. Контейнер читает порт из `PORT`, по умолчанию использует `8000`.

В Jenkins нужно создать задачу **Pipeline → Pipeline script from SCM**, указать Git-репозиторий, ветку `main` и Script Path `software-development/HW1/Jenkinsfile`. Jenkins-агенту нужны Python, Ruff из `requirements-ci.txt`, Docker с Compose и `curl`. Агент должен работать на том же хосте, где Docker публикует порт `8081`. Первый запуск можно сделать через **Build Now**. После него Jenkins проверяет изменения в Git каждые несколько минут через `pollSCM`. Чтобы показать отдельный запуск для каждого коммита, отправляйте по одному коммиту и дожидайтесь, пока Jenkins увидит изменение.

Для задачи нужны два credentials:

- `dockerhub` типа **Username with password**. Пользователь Docker Hub и токен с правом отправки образов в репозиторий `<логин>/ci-demo`.
- `ci-db-password` типа **Secret text**. Пароль для учебной базы PostgreSQL.

Порядок стадий в [Jenkinsfile](Jenkinsfile):

1. **Lint** и **Test** проверяют код и запускают юнит-тесты.
2. **Build** собирает Docker-образ, **Publish** отправляет его в Docker Hub с тегом SHA коммита.
3. **Migrate database** ждёт запуска PostgreSQL и вызывает `flyway migrate` через [Docker Compose](compose.yaml). `V1` создаёт таблицу `service_settings`, `V2` добавляет строку `temperature_unit = fahrenheit`. Flyway записывает применённые версии в `flyway_schema_history`. База хранится в Docker volume и при следующем запуске уже применённые миграции пропускаются.
4. **Deploy** запускает новую версию и проверяет ответ `/health`. Если миграция завершится ошибкой, Jenkins остановит пайплайн до этой стадии.

SQL демонстрирует отдельный шаг развёртывания. Для вычисления температуры сервису база не нужна.

Те же шаги можно повторить вручную с Docker Compose. Перед запуском нужно задать `DB_PASSWORD` в локальном `.env` или через переменную окружения.

```bash
docker build -t netology-ci-demo:local .
docker compose up -d --wait db
docker compose run --rm migrate
docker compose up -d --wait app
curl -fsS http://127.0.0.1:8081/health
docker compose exec -T db psql -U ci_demo -d ci_demo \
  -c 'SELECT version, description, success FROM flyway_schema_history ORDER BY installed_rank;' \
  -c 'TABLE service_settings;'
```

## 7. Релиз и список изменений

В [ci-cd-release.yml](../../.github/workflows/ci-cd-release.yml) отдельный триггер на теги `ci-cd-v*`. В задаче запускаются тесты, собирается `ci-demo.pyz`, затем Git формирует список коммитов по файлам работы. Для первого релиза берётся история этих файлов до тега, для следующих — изменения после предыдущего достижимого тега `ci-cd-v*`. GitHub CLI создаёт релиз, помещает список изменений в описание и прикрепляет `ci-demo.pyz` к **Assets**.

Пример первого тега после публикации кода на GitHub:

```bash
git tag -a ci-cd-v0.1.0 -m 'CI/CD practice v0.1.0'
git push origin ci-cd-v0.1.0
```

[Проверки и скриншоты для сдачи](EVIDENCE.md).
