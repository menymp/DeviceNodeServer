# event_reactor/handlers/rfid/Dockerfile
FROM localhost:5000/local/docker_base_image:dev


# Shared modules are mounted at runtime by the docker utils file

# copy handler code
COPY ConfigsUtils  /app/ConfigsUtils
COPY DButils  /app/DButils
COPY DockerUtils  /app/DockerUtils

COPY event_reactor/handlers/rfid/worker.py /app/worker.py

ENV PYTHONUNBUFFERED=1
USER root
WORKDIR /app
# Dockerfile approach: keep container alive after script fails
ENTRYPOINT ["python", "worker.py"]

#
# docker compose build --no-cache reactor-service
# docker compose up -d --force-recreate reactor-service
#
