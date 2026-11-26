
Запускаем TrackNode 2.0 локально через Docker, с отдельной базой данных, чтобы не затрагивать основной проект.
1. Запуск Backend и Frontend
В терминале VS Code, находясь в папке tracknode2.0, выполни:
cd ydro


Убедись, что Docker Desktop запущен, затем выполни:
docker compose -p tracknode20 -f docker-compose.yml -f docker-compose.studio.yml up --build -d postgres redis backend frontend


2. Выполняем миграции базы данных
docker compose -p tracknode20 exec backend python manage.py migrate


3. Проверяем состояние контейнеров
docker compose -p tracknode20 ps


4. Открываем проект
Сервис	Адрес
Frontend	localhost:8001
Backend	localhost:8000/api/
TrackNode Studio	localhost:8001/studio
Django Admin	localhost:8000/admin/

5. Просмотр логов при ошибках
Backend:
docker compose -p tracknode20 logs -f backend


Frontend:
docker compose -p tracknode20 logs -f frontend


6. Остановка проекта
docker compose -p tracknode20 -f docker-compose.yml -f docker-compose.studio.yml down