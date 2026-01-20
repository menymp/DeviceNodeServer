FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ../DBUtils/ ./DBUtils/
COPY ../ConfigUtils/ ./ConfigUtils/
COPY ../DockerUtils/ ./DockerUtils/
COPY ../WSocketServerManager/ ./WSocketServerManager/

CMD ["python", "WSocketServerManager/main.py"]