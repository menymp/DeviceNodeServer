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
COPY ./deviceNodeServer/DeviceMainNodeServer/VideoHandler/requirements.txt .
RUN pip install --upgrade pip \ 
 && pip install -r requirements.txt

# Copy shared modules from inside DeviceMainNodeServer
COPY ./deviceNodeServer/DeviceMainNodeServer/ConfigsUtils ./ConfigsUtils
COPY ./deviceNodeServer/DeviceMainNodeServer/DButils ./DButils
COPY ./deviceNodeServer/DeviceMainNodeServer/DockerUtils ./DockerUtils

# Copy the service code itself
COPY ./deviceNodeServer/DeviceMainNodeServer/VideoHandler ./VideoHandler

CMD ["python", "VideoHandler/main.py"]
