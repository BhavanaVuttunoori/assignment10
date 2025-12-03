# 📦 Project Setup

---

# 🧩 1. Install Homebrew (Mac Only)

> Skip this step if you're on Windows.

Homebrew is a package manager for macOS.  
You’ll use it to easily install Git, Python, Docker, etc.

**Install Homebrew:**

```markdown
# assignment10 — Secure User Model + Tests + CI/CD

This repository contains a FastAPI application that implements a secure SQLAlchemy user model, Pydantic validation, automated tests (unit + integration), and a CI/CD pipeline that builds and (optionally) publishes a Docker image to a container registry.

This README explains how to set up the project from scratch, run the application and tests locally, and configure CI/CD deployment. Follow each step below.

---

## Prerequisites

- Python 3.10 or newer
- pip
- git (for source control operations)
- Docker & docker-compose (required to run integration tests locally and to build images)

Optional (for Playwright end-to-end tests):
- Playwright browsers will be installed in CI or locally when requested.

---

## 1 — Create and activate a Python virtual environment

Keep your environment isolated with a venv.

```bash
python3 -m venv .venv
source .venv/bin/activate    # macOS / Linux
# .venv\Scripts\activate    # Windows (PowerShell/CMD alternative)
```

Upgrade pip and install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 2 — Provide runtime secrets (local development)

The application reads configuration from environment variables. A convenient local approach is a `.env` file placed at the repository root. An example file ` .env.example` is included.

Create your `.env` and add a secure SECRET_KEY:

```bash
cp .env.example .env
python -c "import secrets, json; print(secrets.token_urlsafe(32))"
# Edit .env and paste the printed value as SECRET_KEY
```

Important: `.env` is in `.gitignore` by default. Do not commit real secrets to version control.

Key environment variables used by the app and tests:
- SECRET_KEY — secret used for token creation
- DATABASE_URL — SQLAlchemy database URL for integration tests or running the app
- POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB — used by docker-compose or CI Postgres service

---

## 3 — Run the application locally

If you want to run the FastAPI app locally (no Docker):

```bash
source .venv/bin/activate
# Ensure DATABASE_URL is set (example: SQLite for local quick runs)
export DATABASE_URL="sqlite:///./test.db"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in your browser (or the app's root) to verify the API.

Notes:
- For full integration with Postgres, use the Docker Compose instructions below.

---

## 4 — Run unit tests (fast)

Unit tests exercise pure-Python logic like password hashing and Pydantic validation.

```bash
source .venv/bin/activate
pytest tests/unit/ -q
```

If tests fail locally due to a compiled native dependency, run them in CI (Actions) where the environment is a clean Ubuntu runner.

---

## 5 — Run integration tests locally (Postgres)

Integration tests need a running Postgres instance. Use Docker Compose to start the DB service.

Start Postgres (example `docker-compose.yml` is included):

```bash
docker-compose up -d postgres
# Wait for the DB to be healthy (or use `docker-compose ps`)
export DATABASE_URL=postgresql://user:password@localhost:5432/mytestdb
pytest tests/integration/ -q
```

When finished:

```bash
docker-compose down
```

---

## 6 — Build and run the Docker image locally

Build the image:

```bash
docker build -t <your-docker-username>/assignment10:local .
```

Run the container (override DATABASE_URL via env):

```bash
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@db:5432/mytestdb" \
  <your-docker-username>/assignment10:local
```

Test the running service at http://localhost:8000.

---

## 7 — CI/CD on GitHub Actions (what the pipeline does)

The provided workflow implements three stages:

1) `test` job
- Runs on `ubuntu-latest`.
- Starts a Postgres service (Docker image) for integration tests.
- Installs Python dependencies and Playwright browsers (if e2e tests are used).
- Sets `DATABASE_URL` to point at the service and runs unit and integration tests.

2) `security` job
- Builds a local Docker image in the job and scans it with Trivy for high/critical vulnerabilities.

3) `deploy` job (runs only on `main` and after security)
- Logs into a container registry and pushes the built image with tags `latest` and `sha`.

Secrets required by the workflow (when using Docker Hub):
- `DOCKERHUB_USERNAME` — Docker Hub username
- `DOCKERHUB_TOKEN` — Docker Hub access token (recommended) or password

If you prefer to avoid Docker Hub credentials, the workflow can be modified to push to GitHub Container Registry (GHCR) using the built-in `GITHUB_TOKEN` (no extra secrets). Ask to switch to GHCR and the workflow will be updated accordingly.

---

## 8 — Add repository secrets for deploy (Docker Hub)

1. Create a Docker Hub access token:
   - On Docker Hub, go to Account Settings → Security → New Access Token.
   - Copy the token value.

2. In GitHub repository settings → Secrets and variables → Actions, add two secrets:
   - `DOCKERHUB_USERNAME` = your Docker Hub username
   - `DOCKERHUB_TOKEN` = the token you created

Once added, a push to `main` will trigger the full pipeline and (if all checks pass) push images to Docker Hub.

---

## 9 — How to interpret CI results and collect screenshots for submission

- After pushing your code, open the repository's Actions tab and click the latest workflow run.
- Verify the `test` job completes successfully (green check). Save a screenshot of the run summary.
- Verify the `security` job scanned the image without fatal findings (or with acceptable results per assignment). Save a screenshot.
- Verify the `deploy` job completed and the Docker image was pushed to the registry. Open your Docker Hub (or GHCR) repository and capture a screenshot showing the pushed tags.

Include these screenshots in your submission materials.

---

## 10 — Submission checklist (what to include)

- A link to this GitHub repository (public or accessible per instructor guidelines).
- Screenshots of:
  - Successful GitHub Actions workflow run
  - Docker Hub (or GHCR) showing the pushed image and tags
- `REFLECTION.md` describing challenges, what you learned, and any deviations
- README updated with the test/run instructions (this file)

---

## Troubleshooting notes

- If unit tests fail locally due to a compiled native dependency (e.g., cryptography), prefer running tests on the GitHub Actions runner which provides a clean environment.
- If integration tests fail, verify the Postgres service is healthy and `DATABASE_URL` is pointing at the expected host/port.
- For Docker-related failures, rebuild images with `--no-cache` to avoid stale layers:

```bash
docker build --no-cache -t <image> .
```

---

## Contact / Next steps

- If you want me to push the prepared commits and trigger CI, tell me whether you want the deploy to target Docker Hub (you will add secrets) or GHCR (no extra secrets). I can update the workflow and push accordingly.

Good luck — follow the steps in order and CI will validate the integration tests and container build on a clean runner.

```

