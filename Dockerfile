FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home launcher \
    && mkdir /data \
    && chown launcher:launcher /data
COPY main.py email_content.html ./

USER launcher
WORKDIR /data
CMD ["python", "/app/main.py"]
