```markdown
# AQI History Scraper + GPT-4o Summarizer (Starter)

What it does
- Collects historical AQI/observation records from public sources (OpenAQ, AirNow example).
- Stores time series in SQLite.
- Uses GPT-4o to summarize trends, detect exceedance events, and produce short, actionable notes.

Important notes
- Always obey API rate limits, Terms of Service and robots.txt. Prefer official APIs (OpenAQ, AirNow) over scraping.
- Do NOT bypass paywalls or protections.
- Add proper error handling, retries, and backoff for production.

Environment variables (create a .env file)
- OPENAI_API_KEY=sk-...
- AIRNOW_API_KEY=... (optional; used if you enable AirNow client)
- USER_AGENT="your-app/1.0 (contact@example.org)"

Quick start
1. Install: python -m pip install -r requirements.txt
2. Configure .env
3. Run (example): python main.py --source openaq --location "Seattle, WA" --start 2026-01-01 --end 2026-01-15
4. DB file: aqi_history.db (inspect with sqlite-utils or SQLite browser)

Extending
- Add other API clients under `scraper/`.
- Add Playwright if you must scrape JS-heavy dashboards.
- Add scheduling (cron, systemd, or Prefect/Airflow) to collect daily history.

```