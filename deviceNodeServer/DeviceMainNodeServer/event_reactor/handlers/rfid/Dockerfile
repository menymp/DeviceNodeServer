# event_reactor/handlers/rfid/Dockerfile
FROM registry.local/docker_base_image:latest


# Copy shared modules from inside DeviceMainNodeServer
COPY ./deviceNodeServer/DeviceMainNodeServer/ConfigsUtils ./ConfigsUtils
COPY ./deviceNodeServer/DeviceMainNodeServer/DButils ./DButils
COPY ./deviceNodeServer/DeviceMainNodeServer/DockerUtils ./DockerUtils

# copy handler code
COPY worker.py /app/worker.py

ENV PYTHONUNBUFFERED=1
USER root

ENTRYPOINT ["python", "app/worker.py"]