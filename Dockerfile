# Stage 1: Build
FROM python:3.10-slim as build
WORKDIR /app

COPY run.sh .env.docker ./
RUN "chmod +x run.sh"
RUN "mv .env.docker .env"

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry install --no-root

COPY . .
EXPOSE 8000

CMD ["sh", "-c", "run.sh"]


