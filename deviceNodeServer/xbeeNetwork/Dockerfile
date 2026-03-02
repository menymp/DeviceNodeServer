FROM python:3.11-slim
WORKDIR /app

# Copy requirements file from the service folder
COPY ./deviceNodeServer/xbeeNetwork/requirements.txt .
RUN pip install -r requirements.txt

# Copy shared modules from inside DeviceMainNodeServer
COPY ./deviceNodeServer/DeviceMainNodeServer/Libraries ./Libraries
COPY ./deviceNodeServer/xbeeNetwork ./xbeeNetwork

CMD ["python", "xbeeNetwork/main.py"]
