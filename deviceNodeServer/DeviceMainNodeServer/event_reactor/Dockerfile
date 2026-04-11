# deviceNodeServer/DeviceMainNodeServer/event_reactor/Dockerfile
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
  && rm -rf /var/lib/apt/lists/*

# copy only requirements so layer is cached unless requirements change
COPY ./deviceNodeServer/DeviceMainNodeServer/event_reactor/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
 && pip install -r /app/requirements.txt

# create app dir and copy wait script (so it's available even when code is mounted)
COPY ./deviceNodeServer/DeviceMainNodeServer/event_reactor/wait_for_images.sh /usr/local/bin/wait_for_images.sh
RUN chmod +x /usr/local/bin/wait_for_images.sh

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# default entrypoint runs the reactor; source will be mounted over /app/event_reactor in dev
ENTRYPOINT ["/bin/sh", "-c", "/usr/local/bin/wait_for_images.sh && exec python /app/event_reactor/start_reactor.py"]
