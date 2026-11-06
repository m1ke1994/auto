# Подключение сайта Александра Водопьянова к TrackNode

Источник сайта: https://github.com/m1ke1994/vodopyanov-site
Публичный домен: https://stariy-site.ru/
TrackNode slug: `vodopyanov`
Сборка сайта закреплена на коммите `c62cbd5295425d14b53bb17ccd3642a363b1383e`.

## Безопасность

- Существующие таблицы и миграции не изменяются. Создаются только новые записи Site и SiteSection для vodopyanov.
- Для нового сайта создаётся отдельная запись Site с отдельным api_key; владелец — текущий владелец сайта tracknode.
- Код трекера подключается только после явного разрешения аналитики посетителем.
- Все 3 HTML-страницы и 3D WebGL остаются в отдельном репозитории.
- Контент загружается из десяти редактируемых секций TrackNode: первый экран, слово, автор, стихи, песни, послесловие, контакты.
- В редакторе доступны добавление/удаление стихов и песен, текст, даты, фото автора и ссылки на аудио. Загрузка MP3 в медиатеку TrackNode пока не поддерживается (используйте HTTPS URL).

## Публикация

1. Проверить, что DNS A-записи `stariy-site.ru` и `www.stariy-site.ru` ведут на **публичный IPv4 самого сервера**, а TCP 80/443 доступны извне.
2. Поставить автодеплой на паузу: `sudo systemctl stop yadro-autodeploy.timer`.
3. Проверить чистый Git: `git status --short`. Существующие локальные шаблоны других сайтов должны быть сохранены и не перезаписаны.
4. `bash scripts/deploy-vodopyanov-site.sh` — проверяемая резервная копия БД, сборка и запуск только `vodopyanov_site`, затем проверка и плавная перезагрузка конфигурации существующего Nginx (без пересоздания контейнера).
5. Проверить HTTP-01 до сертификата:

   ```bash
   mkdir -p ydro/docker/nginx/templates-https/.well-known/acme-challenge
   echo ping-vodopyanov > ydro/docker/nginx/templates-https/.well-known/acme-challenge/check
   curl -f http://stariy-site.ru/.well-known/acme-challenge/check
   curl -f http://www.stariy-site.ru/.well-known/acme-challenge/check
   ```

6. Только после успешных проверок выпустить сертификат на **хосте**, не внутри Docker:

   ```bash
   sudo certbot certonly --webroot \
     -w /home/alex/auto/auto/ydro/docker/nginx/templates-https \
     -d stariy-site.ru -d www.stariy-site.ru
   ```

7. `bash scripts/activate-vodopyanov-https.sh` — проверка сертификата, включение HTTPS-шаблона с `nginx -t` и перезагрузка Nginx **без перезапуска PostgreSQL**.
8. `bash scripts/register-vodopyanov-site.sh --check`, затем `bash scripts/register-vodopyanov-site.sh --apply`. Скрипт собирает новый образ backend, запускает отдельную команду без рестарта работающего backend и миграций, создаёт только отсутствующие секции с сохранением существующих изменений.
9. Проверить `https://tracknode.ru/api/sites/vodopyanov/` (не публикуйте ключ в логах), открыть `https://stariy-site.ru/`, согласиться на аналитику и проверить получение визита в кабинете TrackNode. Затем в разделе «Содержимое сайта» изменить тестовый заголовок, сохранить, перезагрузить stariy-site.ru и убедиться, что текст обновился.

Не включайте общий `yadro-autodeploy.timer` без аудита `/home/alex/auto/deploy.sh`: его действия отличаются от безопасного изолированного деплоя.

## Обновление только сайта Водопьянова (после первоначального SSL)

Не запускать общий deploy.sh, compose down, миграции или seed-скрипты других сайтов.

```bash
cd /home/alex/auto/auto
sudo systemctl stop yadro-autodeploy.timer
git status --short
git pull --ff-only origin main
bash scripts/update-vodopyanov-site.sh
```

Скрипт собирает отдельно образ `vodopyanov_site`, проверяет и добавляет **только отсутствующие** CMS-разделы (теперь всего 10), предварительно создаёт резервную копию БД и пересоздаёт **только** контейнер `vodopyanov_site`. Общий Nginx, backend, PostgreSQL и другие сайты не перезапускаются.

В TrackNode появятся разделы «Страница „Все стихи“», «Страница „Все песни“» и «Главная — SEO». Редактирование самих стихов/песен по-прежнему в существующих «Стихотворения» и «Песни». Изменения кода не перезаписывают уже сохранённые произведения, фотографии, биографию и контакты.

SEO Title и Description, заданные в TrackNode, изменяются на страницах **после загрузки браузером JS**; для поисковых роботов сохранены отдельные статические SEO-метаданные, canonical, Open Graph и JSON-LD на всех трёх страницах. Для гарантированного серверного отражения последующих SEO-правок понадобится отдельный SSR/prerender workflow.

## Исправление favicon (2026-11-06)

Используются иконки /favicon.ico, /favicon-32.png, /favicon-16.png. В HTML всех трёх страниц записаны уникальные URL с версией для обхода кэша браузера. Nginx контейнера сайта возвращает для этих иконок Cache-Control: no-cache. Изолированное обновление автора проверяет HTTP-доступность каждой иконки; другие сайты и БД не затрагиваются.
