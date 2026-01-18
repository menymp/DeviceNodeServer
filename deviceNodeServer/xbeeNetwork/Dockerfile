FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ../Libraries ./Libraries
COPY ../xbeeNetwork ./xbeeNetwork

CMD ["python", "xbeeNetwork/main.py"]