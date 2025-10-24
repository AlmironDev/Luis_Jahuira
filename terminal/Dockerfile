FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para cache
COPY requirements.txt .

# Usar mirror de pip y aumentar timeout
RUN pip install --no-cache-dir \
    --timeout 300 \
    --retries 5 \
    --index-url https://pypi.org/simple/ \
    -r requirements.txt

# Copiar el código de la aplicación
COPY . .

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["python", "app.py"]