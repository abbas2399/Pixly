FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run collectstatic at build time so cold starts are faster
RUN SECRET_KEY=build-dummy python manage.py collectstatic --noinput

EXPOSE 8080

RUN chmod +x start.sh
CMD ["sh", "start.sh"]
