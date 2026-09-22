# Task API

A REST API for managing a to-do list, built with Python and FastAPI.

The project uses PostgreSQL for persistent task storage, Docker Compose to run the application stack, and Supabase Auth for user authentication. Protected endpoints verify JSON Web Tokens (JWTs) before allowing access.

## Features

- Create, read, update, and delete tasks
- PostgreSQL persistent data storage
- Dockerized FastAPI and PostgreSQL stack
- User signup and login with Supabase Auth
- JWT bearer-token authentication
- Protected API routes
- User logout
- Interactive Swagger UI with bearer authentication

## Technologies Used

- Python
- FastAPI
- PostgreSQL
- Docker
- Docker Compose
- Supabase Auth
- Pydantic
- Swagger UI
- Git and GitHub

## Environment Variables

Create a `.env` file in the project root.

The required variables are:

```env
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/YOUR_DATABASE
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_key
```

A `.env.example` file is included as a template.

The real `.env` file is excluded from Git using `.gitignore` so credentials and Supabase configuration are not committed to the repository.

## Run the Application

Make sure Docker Desktop is running.

Start the complete FastAPI and PostgreSQL stack with:

```bash
docker compose up --build
```

The API will be available at:

`http://localhost:8000`

Swagger UI is available at:

`http://localhost:8000/docs`

To stop the containers:

```bash
docker compose down
```

## API Endpoints

| Method | Endpoint | Description | Authentication |
|---|---|---|---|
| GET | `/` | Get API information | No |
| GET | `/health` | Check API health | No |
| POST | `/auth/signup` | Create a Supabase user account | No |
| POST | `/auth/login` | Log in and receive an access token | No |
| POST | `/auth/logout` | Log out the authenticated user | Yes |
| GET | `/public/info` | Get public information | No |
| GET | `/protected/profile` | Get authenticated user profile | Yes |
| GET | `/protected/dashboard` | Get protected dashboard information | Yes |
| GET | `/tasks` | Get all tasks | Yes |
| GET | `/tasks/{task_id}` | Get a specific task | No |
| POST | `/tasks` | Create a new task | No |
| PUT | `/tasks/{task_id}` | Update an existing task | No |
| DELETE | `/tasks/{task_id}` | Delete a task | No |

## Authentication

Authentication is handled by Supabase Auth.

Users first create an account using:

`POST /auth/signup`

They can then log in using:

`POST /auth/login`

A successful login returns a JWT access token. Protected routes require this token to be sent using the HTTP Authorization header:

```text
Authorization: Bearer <access_token>
```

The FastAPI authentication dependency verifies the token with Supabase before allowing access to protected endpoints.

Invalid or expired tokens are rejected with `401 Unauthorized`.

## Swagger Bearer Authentication

FastAPI automatically generates interactive API documentation using Swagger UI.

Open:

`http://localhost:8000/docs`

Click **Authorize** and paste the access token returned by `/auth/login`.

After authorization, Swagger automatically sends the bearer token when calling protected endpoints.

### Authentication in Swagger UI

![Swagger Bearer Authentication](images/swagger-auth.png)

## PostgreSQL Database

Task data is stored in PostgreSQL.

Docker Compose runs two services:

- `api` — the FastAPI application
- `db` — the PostgreSQL database

The API connects to PostgreSQL using the `DATABASE_URL` environment variable.

The `tasks` table is automatically created when the application starts and is seeded with example tasks if the table is empty.

## Database Persistence

PostgreSQL data is stored in a named Docker volume.

This allows task data to survive container restarts:

```bash
docker compose down
docker compose up -d
```

## Previous SQLite Stage

The project previously used SQLite before being migrated to PostgreSQL.

SQLite was used to demonstrate persistent local storage and SQL queries before the application was containerized.

Example query:

```sql
SELECT * FROM tasks WHERE done = TRUE;
```

### SQLite Database Preview

![SQLite tasks database](images/sqlite-database.png)

## Status Codes

| Status Code | Meaning |
|---|---|
| `200 OK` | Request completed successfully |
| `201 Created` | A resource or user was successfully created |
| `204 No Content` | Resource deleted or user logged out successfully |
| `400 Bad Request` | Required or valid input was not provided |
| `401 Unauthorized` | Authentication token is missing, invalid, or expired |
| `404 Not Found` | Requested resource does not exist |

## Security

Passwords are never stored by this API. User credentials are handled by Supabase Auth.

Supabase access tokens are verified before protected endpoints are executed.

The `.env` file is excluded from Git, and `.env.example` contains only placeholder values.