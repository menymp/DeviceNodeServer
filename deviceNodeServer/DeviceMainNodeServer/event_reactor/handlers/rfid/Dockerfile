# event_reactor/handlers/rfid/Dockerfile
FROM localhost:5000/local/docker_base_image:dev


# Shared modules are mounted at runtime by the docker utils file

# copy handler code
COPY worker.py /app/worker.py

ENV PYTHONUNBUFFERED=1
USER root

ENTRYPOINT ["python", "/app/worker.py"]