# aidb
#docker build . -t ai:latest
docker run --rm -ti -v ./src:/home/work/aidb --env-file .env aidb:latest bash