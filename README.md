# 🤖 GenAI Document Agent — Django Edition

AI-powered job search and resume optimiser. Originally built with Streamlit;
UI layer replaced with **Django** for a proper request/response web architecture.

---

## Project Structure

```
GenAI-Document-Agent/
├── manage.py                    # Django entry point
├── core/                        # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── web/                         # Django app (views, templates, static)
│   ├── views.py
│   ├── urls.py
│   ├── templates/web/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── job_search.html
│   │   └── resume_optimizer.html
│   └── static/web/
│       ├── css/main.css
│       └── js/main.js
├── src/                         # Business logic (unchanged)
│   ├── config.py
│   ├── services/
│   │   ├── job_search.py
│   │   ├── job_scorer.py
│   │   ├── job_scraper.py
│   │   ├── llm.py
│   │   └── resume_generator.py
│   └── utils/
│       ├── pdf.py
│       ├── text.py
│       └── decorators.py
├── tests/
├── requirements.txt
└── Makefile
```

---

## Quick Start

```bash
# 1. Clone & create venv
python -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure env
cp .env.example .env
# Edit .env — add OPENAI_API_KEY and SERPER_API_KEY

# 4. Run migrations (sets up file-based sessions — no database needed)
python manage.py migrate --run-syncdb

# 5. Start the server
python manage.py runserver

# Open http://localhost:8000
```

Or with `make`:
```bash
make install
make migrate
make run
```

---

## Pages

| URL | Description |
|-----|-------------|
| `/` | Landing page |
| `/job-search/` | Upload resume + query → ranked job list |
| `/resume-optimizer/` | Paste job URL + resume → tailored resume & cover letter PDF |
| `/download/resume/` | Download optimized resume PDF |
| `/download/cover/` | Download cover letter PDF |

---

## Why Django instead of Streamlit?

| Concern | Streamlit | Django |
|---------|-----------|--------|
| Multiple users | Shared session state issues | Proper per-request isolation |
| URL routing | Single-page only | Full URL structure |
| HTML control | Limited widget API | Full template control |
| Deployment | Streamlit Cloud / manual | Any WSGI host (Heroku, Railway, VPS) |
| Testability | Hard to unit-test UI | Views are plain Python functions |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Required |
| `SERPER_API_KEY` | — | Required |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model |
| `DJANGO_SECRET_KEY` | insecure default | Set in production |
| `DJANGO_DEBUG` | `True` | Set to `False` in production |
| `DJANGO_ALLOWED_HOSTS` | `localhost 127.0.0.1` | Space-separated |
