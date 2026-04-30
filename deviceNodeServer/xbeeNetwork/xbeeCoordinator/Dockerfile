FROM python:3.11-slim
WORKDIR /app

# Copy requirements file from the service folder
COPY ./deviceNodeServer/xbeeNetwork/xbeeCoordinator/requirements.txt .
RUN pip install --upgrade pip \ 
 && pip install -r requirements.txt

# Copy shared modules from inside DeviceMainNodeServer
#COPY ./deviceNodeServer/DeviceMainNodeServer/ConfigsUtils ./ConfigsUtils
#COPY ./deviceNodeServer/DeviceMainNodeServer/DButils ./DButils
#COPY ./deviceNodeServer/DeviceMainNodeServer/DockerUtils ./DockerUtils


#COPY ./deviceNodeServer/xbeeNetwork/xbeeCoordinator ./xbeeCoordinator

CMD ["ls", "./xbeeCoordinator"]
CMD ["python", "xbeeCoordinator/main.py"]




