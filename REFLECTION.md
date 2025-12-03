## Reflection — Module 10

Work completed:

- Implemented a secure SQLAlchemy User model with a `password_hash` column and write-only `password` setter that hashes on assignment.
- Added Pydantic schemas for user creation and response/reading (kept `UserResponse` and added `UserRead` alias).
- Centralized configuration in `app/config.py` to read from environment variables and provided `.env.example`.
- Updated `docker-compose.yml` to accept env-substituted DB credentials.
- Hardened tests a bit for running in constrained environments (fallback Faker and skipping Playwright when not present).
- Adjusted GitHub Actions workflow to set DATABASE_URL at runtime instead of embedding the URL into YAML.

Challenges:

- Running the full test suite in this environment encountered native dependency issues (cryptography / PyJWT / pydantic compiled extensions) that caused import errors and ultimately a `Bus error`. This is environment-specific and didn't block completing code changes — CI on GitHub Actions is the recommended place to run the complete test suite since the runner there installs compiled dependencies correctly.

Next steps I recommend you perform locally or on GitHub:

1. Add repository secrets on GitHub (Settings -> Secrets):
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`
   (Optional) `DATABASE_URL` if you prefer a custom DB connection.

2. Push the current branch to GitHub and confirm CI runs. Capture screenshots of a successful workflow run and Docker push for submission.

3. If you want full local testing with integration tests, run `docker-compose up -d` and then `pytest -q`; otherwise rely on CI for integration-level validation.

4. Update README with your Docker Hub repository link once you have pushed the image.

This reflection will be included in the repository for graders to review.
