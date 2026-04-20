# Blodgett Pool Calendar Feed

This project scrapes the `MAC Pool & Blodgett Pool` accordion on the Harvard Recreation facility-hours page and publishes a subscribable ICS feed for Blodgett Pool only.

## Use the calendar

Site:
[https://logan-blaine.github.io/blodgett-cal/](https://logan-blaine.github.io/blodgett-cal/)

Direct ICS feed:
[https://logan-blaine.github.io/blodgett-cal/blodgett-pool.ics](https://logan-blaine.github.io/blodgett-cal/blodgett-pool.ics)

Harvard Recreation source page:
[https://recreation.gocrimson.com/sports/2021/5/14/facility-hours](https://recreation.gocrimson.com/sports/2021/5/14/facility-hours)

To subscribe in a calendar app, use the direct ICS feed URL above as a calendar subscription URL.

## Local usage

```bash
uv sync --extra dev
uv run blodgett-cal build --output site
```

The generated feed is written to `site/blodgett-pool.ics`, with a landing page at `site/index.html`.

Useful flags:

```bash
uv run blodgett-cal build --output site --now 2026-03-16T09:00:00-04:00
uv run blodgett-cal build --output site --skip-outside-refresh-window
uv run blodgett-cal build --source-url https://recreation.gocrimson.com/sports/2021/5/14/facility-hours
```

## Deployment

GitHub Actions builds and deploys the `site/` directory to GitHub Pages. Scheduled runs refresh every two hours between `6am` and `6pm` Eastern Time.

After GitHub Pages is enabled with `Source = GitHub Actions`, the public URLs are:

- Site: `https://logan-blaine.github.io/blodgett-cal/`
- Feed: `https://logan-blaine.github.io/blodgett-cal/blodgett-pool.ics`
