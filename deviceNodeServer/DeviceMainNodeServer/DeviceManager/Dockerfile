FROM python:3.11-slim
WORKDIR /app

# Copy requirements file from the service folder
COPY ./deviceNodeServer/DeviceMainNodeServer/DeviceManager/requirements.txt .
RUN pip install --upgrade pip \ 
 && pip install -r requirements.txt

# Copy shared modules from inside DeviceMainNodeServer
COPY ./deviceNodeServer/DeviceMainNodeServer/ConfigsUtils ./ConfigsUtils
COPY ./deviceNodeServer/DeviceMainNodeServer/DButils ./DButils
COPY ./deviceNodeServer/DeviceMainNodeServer/DockerUtils ./DockerUtils

# Copy the service code itself
COPY ./deviceNodeServer/DeviceMainNodeServer/DeviceManager ./DeviceManager

CMD ["python", "DeviceManager/main.py"]

