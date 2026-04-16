# event_reactor/handlers/camera/Dockerfile
FROM localhost:5000/local/docker_base_image:dev

# Shared modules are mounted or copied at build time by reactor build context
COPY ConfigsUtils  /app/ConfigsUtils
COPY DButils       /app/DButils
COPY DockerUtils   /app/DockerUtils

COPY event_reactor/handlers/camera/worker.py /app/worker.py

ENV PYTHONUNBUFFERED=1
USER root
WORKDIR /app
ENTRYPOINT ["python", "worker.py"]

#
# docker compose build --no-cache reactor-service
# docker compose up -d --force-recreate reactor-service
#
