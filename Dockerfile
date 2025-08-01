FROM python:3.10-slim

WORKDIR /app

# Configurações para reduzir uso de memória
ENV PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas requirements para aproveitar cache do Docker
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY app /app

# Porta padrão do Render
EXPOSE 10000

# CORREÇÃO: Use um script de inicialização em vez de passar a porta diretamente
CMD ["python", "/app/main.py"]