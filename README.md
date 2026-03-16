# Blodgett Pool Calendar Feed

This project scrapes the `MAC Pool & Blodgett Pool` accordion on the Harvard Recreation facility-hours page and publishes a subscribable ICS feed for Blodgett Pool only.

## Local usage

```bash
uv sync --extra dev
uv run blodgett-cal build --output site
```

The generated feed is written to `site/blodgett-pool.ics`, with a small landing page at `site/index.html`.

Useful flags:

```bash
uv run blodgett-cal build --output site --now 2026-03-16T09:00:00-04:00
uv run blodgett-cal build --output site --skip-outside-refresh-window
uv run blodgett-cal build --source-url https://recreation.gocrimson.com/sports/2021/5/14/facility-hours
```

## Deployment

GitHub Actions builds and deploys the `site/` directory to GitHub Pages. Scheduled runs happen hourly, but the build command skips outside the target Eastern Time refresh windows of `5am`, `1pm`, and `5pm`.
