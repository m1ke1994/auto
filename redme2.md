cd C:\Users\Alex\Desktop\tracknode2.0\ydro

git pull --rebase --autostash origin tracknode-2.0

if ($LASTEXITCODE -ne 0) { throw "Git pull failed" }

docker compose -p tracknode20 -f docker-compose.yml -f docker-compose.studio.yml up -d --build --force-recreate postgres redis backend frontend

if ($LASTEXITCODE -ne 0) {
    docker compose -p tracknode20 -f docker-compose.yml -f docker-compose.studio.yml logs --tail=100 backend
    throw "Docker startup failed"
}

docker compose -p tracknode20 -f docker-compose.yml -f docker-compose.studio.yml ps