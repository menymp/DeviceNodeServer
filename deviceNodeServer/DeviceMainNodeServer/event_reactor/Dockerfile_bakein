FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file from the service folder
COPY ./deviceNodeServer/DeviceMainNodeServer/event_reactor /app/event_reactor
# COPY ./deviceNodeServer/DeviceMainNodeServer/event_reactor/requirements.txt .
RUN pip install --upgrade pip \ 
 && pip install -r ./event_reactor/requirements.txt

# Copy shared modules from inside DeviceMainNodeServer
COPY ./deviceNodeServer/DeviceMainNodeServer/ConfigsUtils  /app/ConfigsUtils
COPY ./deviceNodeServer/DeviceMainNodeServer/DButils  /app/DButils
COPY ./deviceNodeServer/DeviceMainNodeServer/DockerUtils  /app/DockerUtils

# copy wait script into a standard path and make executable
# COPY ./deviceNodeServer/DeviceMainNodeServer/event_reactor/wait_for_images.sh /usr/local/bin/wait_for_images.sh
RUN chmod +x  /app/event_reactor/wait_for_images.sh

# run the wait script in a shell, then exec the python process
ENTRYPOINT ["/bin/sh", "-c", "/app/event_reactor/wait_for_images.sh && pwd && ls  && exec python /app/event_reactor/start_reactor.py"]