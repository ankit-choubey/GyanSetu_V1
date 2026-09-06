# GyanSetu Backend (Phase 1)

This is the initial backend foundation for the GyanSetu project.

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/docs or GET http://localhost:8000/health.

## Notes

- The configuration reads environment variables from a local `.env` file.
- The default database is development-friendly SQLite when `DATABASE_URL` is not set.
- The design is compatible with PostgreSQL for later production use.
