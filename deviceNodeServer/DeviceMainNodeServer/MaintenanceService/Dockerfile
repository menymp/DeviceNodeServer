FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ../DBUtils/ ./DBUtils/
COPY ../DockerUtils/ ./DockerUtils/
COPY ../MaintenanceService/ ./MaintenanceService/

CMD ["python", "MaintenanceService/main.py"]