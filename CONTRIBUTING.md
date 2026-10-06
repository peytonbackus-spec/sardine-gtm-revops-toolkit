# Contributing

- Company facts live in `config/`. Do not hardcode segments, personas, tools or numbers in code.
- Secrets come from environment variables, never the repo.
- Add or change a module with a test in `tests/`; AI outputs need a prompt eval case.
- If you change segment or persona keys, update `scripts/generate_sample_data.py` and run `make data`.
- Before committing: `make lint demo test`. Sample data must regenerate without a diff.
- Never commit private material (`private-vault/`, real CRM exports, names of real prospects or clients).
- SQL: guard divisions with `NULLIF`, and keep fiscal logic on the `{{FY_START_MONTH}}` placeholder.
