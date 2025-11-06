# Dev image for Django + DRF (autoreload)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# timezony do ułtawienia logów
RUN apt-get update && apt-get install -y tzdata && ln -fs /usr/share/zoneinfo/Europe/Warsaw /etc/localtime && dpkg-reconfigure -f noninteractive tzdata && rm -rf /var/lib/apt/lists/*

WORKDIR /app


COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# Kod aplikacji
COPY backend/ /app/

# Entrypoint
COPY docker/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

CMD ["/entrypoint.sh"]
