docker stop pizza-db

docker rm pizza-db

docker run --name pizza-db -e POSTGRES_DB=UE_ENS_PROJET -e POSTGRES_USER=pguser -e POSTGRES_PASSWORD=pguser -p 5432:5432 -d postgres:latest

sleep 5
docker exec -i pizza-db psql -U pguser -d UE_ENS_PROJET < server/init.sql