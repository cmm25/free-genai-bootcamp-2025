FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY /app/requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt

COPY /app/. .

EXPOSE 8888

CMD ["python", "chat.py"]