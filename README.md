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

---

## LLM-Powered Task Intent Extraction

The API includes an LLM-powered endpoint that converts an unstructured task description into predictable, validated structured data.

The feature is designed as a single-decision workflow rather than a chatbot: one task description goes in, one structured result comes out, with no conversational memory.

### Endpoint

`POST /extract`

Example request:

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"text":"Fix the login bug before tomorrow'\''s release"}'
```

Example response:

```json
{
  "action": "fix",
  "subject": "login bug",
  "category": "engineering",
  "urgency": "high",
  "confidence": 0.95,
  "needs_review": false
}
```

The output is parsed and validated with Pydantic before it is returned by the API.

### Output Schema

The endpoint returns:

| Field | Description |
|---|---|
| `action` | Short description of the action to perform |
| `subject` | The object or topic of the task |
| `category` | `engineering`, `research`, `writing`, `admin`, `personal`, or `other` |
| `urgency` | `low`, `normal`, or `high` |
| `confidence` | Confidence value between `0.0` and `1.0` |
| `needs_review` | Whether the result requires human review |

When the task cannot be classified reliably, the model is instructed to use `other`, lower its confidence below `0.5`, and set `needs_review` to `true`.

The full input/output contract and classification rules are documented in [`JOB-CARD.md`](JOB-CARD.md).

### Provider and Prompt

The integration uses OpenRouter through the OpenAI Python SDK.

Current model route:

```text
openrouter/free
```

The prompt is stored separately from the application code and versioned in the `prompts/` directory.

Current prompt version:

```text
intent-extraction-v2
```

The user's task text is sent as a separate user message rather than being inserted into the system prompt.

### Reliability Guardrails

The LLM is treated as an unreliable external dependency. The integration includes:

- Pydantic schema validation
- JSON parsing before returning output
- one repair attempt for malformed or schema-invalid responses
- quarantine logging if the repaired response still fails validation
- a 30-second timeout
- retries for timeouts, HTTP 429 responses, and 5xx errors
- no retries for non-recoverable 400, 401, or 403 errors
- exponential backoff with jitter
- token, latency, prompt-version, and repair-count logging
- an `LLM_ENABLED` kill switch
- an `LLM_STUB` mode for testing without a model call

Raw model text is never returned directly to the API client.

### LLM Environment Variables

The LLM integration uses:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
LLM_ENABLED=true
LLM_STUB=0
```

`.env.example` contains placeholder configuration. The real `.env` file is excluded from Git and must not be committed.

### Evaluation

The endpoint was evaluated against eight hand-labelled task descriptions covering engineering, research, writing, administration, personal tasks, different urgency levels, and ambiguous input.

**Evaluation date:** 2026-09-23  
**Prompt version:** `intent-extraction-v2`  
**Result:** **8/8 passed (100%)**

The evaluation uses exact matching for the closed classification fields:

- `category`
- `urgency`
- `needs_review`

For ambiguous cases requiring review, confidence must also be below `0.5`.

`action` and `subject` are inspected manually because semantically equivalent wording may differ while still representing the correct task intent.

The evaluation cases, runner, and recorded results are stored in [`evals/`](evals/).

Prompt v1 scored **6/8 (75%)** under the revised evaluation rubric. The remaining errors involved a flexible weekend deadline and documentation-related work. Prompt v2 clarified the category boundaries and urgency rules, resulting in the recorded **8/8** evaluation run.

### Operational Logging and Cost

Each successful LLM request records:

- prompt version
- model
- prompt tokens
- completion tokens
- total tokens
- duration
- repair count
- estimated cost

Example recorded log:

```json
{
  "prompt_version": "intent-extraction-v1",
  "model": "openrouter/free",
  "prompt_tokens": 450,
  "completion_tokens": 648,
  "total_tokens": 1098,
  "duration_seconds": 7.592,
  "repair_count": 0,
  "estimated_cost_usd": 0.0
}
```

The OpenRouter free model route is treated as **$0.00** for the assignment cost estimate. A production deployment would calculate estimated cost using the pricing of the specific model selected.

### What I'd Fix Next

The next improvement would be more graceful handling of provider quota exhaustion.

During evaluation, the OpenRouter free-tier daily request limit was reached. The client correctly retried the HTTP 429 response according to the retry policy, but once the daily quota was exhausted, the request could not recover and eventually surfaced as an HTTP 500 response.

A production version should translate an exhausted provider rate limit into a controlled API response while retaining retries for transient 429 errors.
