FROM python:3.11-slim

# Отключаем запись pycache и буферизацию
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app/ .

# Открываем порт
EXPOSE 8000

# Запуск приложения через uvicorn
CMD sleep 10 && python -m uvicorn main:app --host 0.0.0.0 --port 8000

