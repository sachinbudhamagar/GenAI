# 🤖 GenAI Document Agent

An intelligent AI-powered agent for document-based Q&A, job searching, and personalised resume/cover letter generation — built with LangChain, OpenAI, and Streamlit.

---

## ✨ Features

- **Smart Job Search** — Searches multiple query variations via the Serper API and ranks results by TF-IDF cosine similarity against your resume.
- **Resume Optimiser** — Scrapes a job posting URL and rewrites your resume to align with it using GPT-4o-mini.
- **Cover Letter Generator** — Produces a tailored cover letter and highlights missing keywords.
- **PDF Export** — Download optimised documents as properly formatted PDFs.
- **Configurable** — All behaviour tunable via environment variables; no hard-coded magic.

---

## 📁 Project Structure

```
genai-document-agent/
├── app.py                      # Streamlit entry point (thin launcher)
├── src/
│   ├── config.py               # Centralised settings (env vars → dataclass)
│   ├── services/
│   │   ├── llm.py              # Lazy-init ChatOpenAI singleton
│   │   ├── job_search.py       # Serper API job search
│   │   ├── job_scorer.py       # TF-IDF cosine similarity ranking
│   │   ├── job_scraper.py      # HTML job-description scraper
│   │   └── resume_generator.py # LLM resume + cover letter generation
│   ├── utils/
│   │   ├── text.py             # clean_markdown, is_valid_url
│   │   ├── pdf.py              # PDF read/write helpers
│   │   └── decorators.py       # retry_request decorator
│   └── ui/
│       ├── main.py             # Page config + tab layout
│       ├── tab_job_search.py   # Job Search tab
│       └── tab_resume_optimizer.py  # Resume Optimizer tab
├── tests/
│   ├── test_utils_text.py
│   └── test_job_scorer.py
├── samples/                    # Example PDF documents for testing
├── docs/                       # Screenshots and additional docs
├── .env.example                # Environment variable template
├── requirements.txt
├── requirements-dev.txt
├── Makefile                    # Common dev commands
└── pyproject.toml              # Tool configuration (ruff, black, mypy, pytest)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [Serper API key](https://serper.dev) (free tier available)

### Installation

```bash
git clone https://github.com/sachinbudhamagar/GenAI-Document-Agent.git
cd GenAI-Document-Agent

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your API keys

streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## ⚙️ Configuration

All settings are controlled via environment variables (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | OpenAI API key (**required**) |
| `SERPER_API_KEY` | — | Serper search API key (**required**) |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `LLM_TEMPERATURE` | `0.3` | LLM sampling temperature |
| `MAX_RETRY_ATTEMPTS` | `3` | HTTP retry attempts |
| `RETRY_DELAY_SECONDS` | `2.0` | Delay between retries |
| `TOP_JOBS_COUNT` | `10` | Number of top-ranked jobs to surface |
| `MAX_JOBS_TO_SCORE` | `30` | Max jobs fed to the scorer |

---

## 🧪 Development

```bash
# Install dev dependencies
make dev

# Run tests
make test

# Run with coverage report
make test-cov

# Lint
make lint

# Auto-format
make format

# Type-check
make typecheck
```

---

## 🚢 Deployment

- **Streamlit Community Cloud** — Connect your GitHub repo for one-click deployment.
- **Docker** — Add a `Dockerfile` based on `python:3.11-slim`, `COPY` the project, `RUN pip install -r requirements.txt`, `CMD streamlit run app.py`.
- **VPS** — Run behind `nginx` + `gunicorn` with a systemd service.

---

## 🤝 Contributing

1. Fork the repo and create a feature branch.
2. Write tests for new logic.
3. Run `make lint && make test` before opening a PR.
4. Follow existing code style (Black + Ruff).

---

## 📄 License

MIT — see `LICENSE`.

---

## 🙏 Acknowledgements

LangChain · Streamlit · OpenAI · Serper · FAISS · ChromaDB · HuggingFace · ReportLab
