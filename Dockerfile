FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY workflows ./workflows
COPY README.md PRODUCT_BRIEF.md .env.example ./

EXPOSE 8000

CMD ["python", "backend/app.py"]
