# Подключение сайта Александра Водопьянова к TrackNode

Источник сайта: https://github.com/m1ke1994/vodopyanov-site
Публичный домен: https://stariy-site.ru/
TrackNode slug: `vodopyanov`
Сборка сайта закреплена на коммите `28cdecf55ce8cf541c20cbd8eb36d42a657bec7a`.

## Безопасность

- Существующие таблицы и миграции не изменяются. Создаются только новые записи Site и SiteSection для vodopyanov.
- Для нового сайта создаётся отдельная запись Site с отдельным api_key; владелец — текущий владелец сайта tracknode.
- Код трекера подключается только после явного разрешения аналитики посетителем.
- Все 3 HTML-страницы и 3D WebGL остаются в отдельном репозитории.
- Контент загружается из семи редактируемых секций TrackNode: первый экран, слово, автор, стихи, песни, послесловие, контакты.
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
