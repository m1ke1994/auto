# Режим владельца платформы TrackNode

Глобальный интерфейс доступен только Django permission `platform_admin.access_platform`. Обычный `is_staff` не предоставляет доступ. Дополнительные чувствительные возможности защищены отдельными permissions:

- `view_platform_personal_data` — персональные данные заявок;
- `view_platform_tracker_key` — ключ трекера;
- `manage_platform_recommendations` — входные данные и технический результат AI, повторный запуск и скрытие.

После стандартного deploy и `python manage.py migrate` назначьте роль существующему пользователю:

```bash
python manage.py grant_platform_owner <username>
```

Команда идемпотентна. Отзыв доступа:

```bash
python manage.py grant_platform_owner <username> --revoke
```

Группа `platform_owner` получает все четыре permission. `is_superuser` обладает ими через стандартную модель Django. Будущим сотрудникам поддержки можно назначать отдельные permissions без включения в группу владельца.

API расположен только под `/api/platform/`; клиентские queryset и URL не изменены. Просмотр сайта владельцем платформы является read-only режимом данных и не создаёт JWT или сессию другого пользователя.

Проверка:

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py test platform_admin
cd vue-admin && npm run build
```
