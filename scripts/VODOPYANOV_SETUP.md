# Подключение сайта Александра Водопьянова к TrackNode

Источник сайта: https://github.com/m1ke1994/vodopyanov-site
Публичный домен: https://stariy-site.ru/
TrackNode slug: `vodopyanov`
Сборка сайта закреплена на коммите `b1c4fd7020ed9a2ea531da5d5f80a3db3fb2c66b`.

## Безопасность

- Существующие таблицы, записи и миграции не изменяются.
- Для нового сайта создаётся отдельная запись Site с отдельным api_key; владелец — текущий владелец сайта tracknode.
- Код трекера подключается только после явного разрешения аналитики посетителем.
- Все 3 HTML-страницы и 3D WebGL остаются в отдельном репозитории.
- Пока контент стихов/песен хранится в исходниках авторского сайта, в TrackNode подключена аналитика, а не редактор произведений.

## Публикация

1. Проверить, что DNS A-записи `stariy-site.ru` и `www.stariy-site.ru` ведут на **публичный IPv4 самого сервера**, а TCP 80/443 доступны извне.
2. Поставить автодеплой на паузу: `sudo systemctl stop yadro-autodeploy.timer`.
3. Проверить чистый Git: `git status --short`. Существующие локальные шаблоны других сайтов должны быть сохранены и не перезаписаны.
4. `bash scripts/deploy-vodopyanov-site.sh` — проверяемая резервная копия БД, сборка и запуск только `vodopyanov_site`, затем пересоздание только общего Nginx для нового ACME bind-mount.
5. Проверить HTTP-01 до сертификата:

   ```bash
   mkdir -p ydro/docker/nginx/acme-challenge/.well-known/acme-challenge
   echo ping-vodopyanov > ydro/docker/nginx/acme-challenge/.well-known/acme-challenge/check
   curl -f http://stariy-site.ru/.well-known/acme-challenge/check
   curl -f http://www.stariy-site.ru/.well-known/acme-challenge/check
   ```

6. Только после успешных проверок выпустить сертификат на **хосте**, не внутри Docker:

   ```bash
   sudo certbot certonly --webroot \
     -w /home/alex/auto/auto/ydro/docker/nginx/acme-challenge \
     -d stariy-site.ru -d www.stariy-site.ru
   ```

7. `bash scripts/activate-vodopyanov-https.sh` — проверка сертификата, включение HTTPS-шаблона с `nginx -t` и перезагрузка Nginx **без перезапуска PostgreSQL**.
8. `bash scripts/register-vodopyanov-site.sh --check`, затем `bash scripts/register-vodopyanov-site.sh --apply`. Это единственная операция записи в БД: добавление **только нового** сайта и привязка клиента.
9. Проверить `https://tracknode.ru/api/sites/vodopyanov/` (не публикуйте ключ в логах), открыть `https://stariy-site.ru/`, согласиться на аналитику и проверить получение визита в кабинете TrackNode.

Не включайте общий `yadro-autodeploy.timer` без аудита `/home/alex/auto/deploy.sh`: его действия отличаются от безопасного изолированного деплоя.
