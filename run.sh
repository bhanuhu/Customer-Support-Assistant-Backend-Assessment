#!/bin/bash

set -e

# run migrations
alembic upgrade head

# run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
