# Customer Support Assistant Backend Assessment

## Project Overview

This project is a backend service for a Customer Support Assistant application, built using FastAPI. It provides a RESTful API for managing tickets, users, and AI-generated responses.


## Local Setup

### Prerequisites

Ensure you have the following installed:
- Python 3.10
- [Poetry](https://python-poetry.org/docs/#installation)

### Setup Without Docker

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/customer-support-assistant.git
   cd customer-support-assistant
   ```

2. **Install Dependencies**
   ```bash
   poetry install
   ```

3. **Set Up Environment Variables**

   Create a `.env` file in the root directory with the following content:
   ```
   POSTGRES_USER=your_postgres_user
   POSTGRES_PASSWORD=your_postgres_password
   POSTGRES_DB=customer_support
   POSTGRES_HOSTNAME=127.0.0.1
   DATABASE_PORT=5432
   GROQ_API_KEY=your_groq_api_key
   ```

4. **Run Migrations**
   ```bash
   poetry run alembic upgrade head
   ```

5. **Start the Server**
   ```bash
   poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Setup With Docker

1. **Ensure Docker is Installed**

   Install Docker from [here](https://docs.docker.com/get-docker/).

2. **Build and Run the Docker Container**
   ```bash
   docker-compose up --build
   ```

## API Endpoints

### Authentication

- **Sign Up**
  - `POST /auth/signup`
  - Request Body: `{ "email": "user@example.com", "password": "securepassword" }`
  - Response: User data

- **Login**
  - `POST /auth/login`
  - Request Body: `{ "email": "user@example.com", "password": "securepassword" }`
  - Response: `{ "access_token": "token", "token_type": "bearer" }`

### Tickets

- **List Tickets**
  - `GET /tickets`
  - Response: List of tickets for the authenticated user

- **Create Ticket**
  - `POST /tickets`
  - Request Body: `{ "subject": "Issue title", "description": "Detailed description" }`
  - Response: Created ticket data

- **Get Ticket Details**
  - `GET /tickets/{ticket_id}`
  - Response: Ticket details

- **Add Message to Ticket**
  - `POST /tickets/{ticket_id}/messages`
  - Request Body: `{ "content": "Message content" }`
  - Response: Added message data

- **AI Response**
  - `GET /tickets/{ticket_id}/ai-response`
  - Response: AI-generated message stream

### Environment Variables

- `POSTGRES_USER`: The PostgreSQL username.
- `POSTGRES_PASSWORD`: The PostgreSQL password.
- `POSTGRES_DB`: The PostgreSQL database name.
- `POSTGRES_HOSTNAME`: The PostgreSQL host address.
- `DATABASE_PORT`: The port for PostgreSQL.
- `GROQ_API_KEY`: The API key for Groq service.

