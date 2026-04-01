FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file from the service folder
COPY ./deviceNodeServer/DeviceMainNodeServer/event_reactor/requirements.txt .
RUN pip install --upgrade pip \ 
 && pip install -r requirements.txt

# Copy shared modules from inside DeviceMainNodeServer
COPY ./deviceNodeServer/DeviceMainNodeServer/ConfigsUtils ./ConfigsUtils
COPY ./deviceNodeServer/DeviceMainNodeServer/DButils ./DButils
COPY ./deviceNodeServer/DeviceMainNodeServer/DockerUtils ./DockerUtils

# Copy the service code itself
COPY ./deviceNodeServer/DeviceMainNodeServer/event_reactor ./event_reactor

RUN chmod +x ./event_reactor/wait_for_images.sh

#CMD ["python", "event_reactor/main.py"]
ENTRYPOINT ["/usr/local/bin/wait_for_images.sh", "&&", "python", "event_reactor/main.py"]