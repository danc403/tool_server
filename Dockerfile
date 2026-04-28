# Debian 13 Trixie Slim
FROM python:3.13-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Use --no-cache-dir to keep the image slim
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m idguser && chown -R idguser /app
USER idguser

EXPOSE 8080

# Syntax: [tool_server WITHOUT .PY]:[VARIABLE NAME]
CMD ["uvicorn", "tool_server:app", "--host", "0.0.0.0", "--port", "8080"]
