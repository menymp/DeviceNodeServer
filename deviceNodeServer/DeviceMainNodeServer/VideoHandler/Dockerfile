FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ../DBUtils ./DBUtils
COPY ../ConfigUtils ./ConfigUtils
COPY ../VideoHandler ./VideoHandler

CMD ["python", "VideoHandler/main.py"]