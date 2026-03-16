from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from zoneinfo import ZoneInfo

from .models import PoolBlock

ET_ZONE = ZoneInfo("America/New_York")


def build_calendar(blocks: list[PoolBlock], source_url: str, generated_at: datetime | None = None) -> str:
    stamp = (generated_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//blodgett-cal//Blodgett Pool Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Blodgett Pool",
        "X-WR-TIMEZONE:America/New_York",
    ]

    for block in blocks:
        lines.extend(build_event(block, source_url, stamp))

    lines.append("END:VCALENDAR")
    return "\r\n".join(fold_ical_line(line) for line in lines) + "\r\n"


def build_event(block: PoolBlock, source_url: str, stamp: datetime) -> list[str]:
    start_local = datetime.combine(block.date_local, block.start_local, tzinfo=ET_ZONE)
    end_local = datetime.combine(block.date_local, block.end_local, tzinfo=ET_ZONE)
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)

    uid_seed = f"{block.date_local.isoformat()}|{block.start_local.isoformat()}|{block.end_local.isoformat()}"
    uid = f"{sha1(uid_seed.encode('utf-8')).hexdigest()}@blodgett-cal"

    description_lines = [f"Source: {source_url}"]
    if block.notes:
        description_lines.append("")
        description_lines.extend(block.notes)

    description = escape_text("\n".join(description_lines))

    return [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{format_utc(stamp)}",
        f"DTSTART:{format_utc(start_utc)}",
        f"DTEND:{format_utc(end_utc)}",
        f"SUMMARY:{escape_text('Blodgett Pool')}",
        f"DESCRIPTION:{description}",
        "END:VEVENT",
    ]


def write_calendar(path: Path, calendar_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(calendar_text, encoding="utf-8")


def render_index(ics_name: str = "blodgett-pool.ics") -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Blodgett Pool Calendar Feed</title>
    <link
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
      rel="stylesheet"
      integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH"
      crossorigin="anonymous"
    >
    <style>
      :root {{
        --blodgett-cream: #f6f0e8;
        --blodgett-crimson: #a51c30;
        --blodgett-ink: #1d1b1a;
        --blodgett-gold: #d8b26e;
      }}

      body {{
        min-height: 100vh;
        color: var(--blodgett-ink);
        background:
          radial-gradient(circle at top left, rgba(216, 178, 110, 0.28), transparent 28%),
          radial-gradient(circle at top right, rgba(165, 28, 48, 0.18), transparent 32%),
          linear-gradient(180deg, #fcfaf7 0%, var(--blodgett-cream) 100%);
      }}

      .hero {{
        background: linear-gradient(135deg, rgba(165, 28, 48, 0.96), rgba(112, 16, 29, 0.96));
        color: #fff8f1;
        border: 1px solid rgba(255, 255, 255, 0.16);
        box-shadow: 0 24px 60px rgba(80, 18, 28, 0.18);
      }}

      .hero-tag {{
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-size: 0.78rem;
        color: rgba(255, 248, 241, 0.8);
      }}

      .panel {{
        border: 0;
        box-shadow: 0 16px 40px rgba(70, 42, 19, 0.08);
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(6px);
      }}

      .feed-box {{
        border: 1px solid rgba(165, 28, 48, 0.16);
        background: rgba(255, 248, 241, 0.92);
      }}

      .feed-input {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.92rem;
      }}

      .step-number {{
        width: 2rem;
        height: 2rem;
        border-radius: 999px;
        background: rgba(165, 28, 48, 0.12);
        color: var(--blodgett-crimson);
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        justify-content: center;
      }}

      .btn-crimson {{
        background: var(--blodgett-crimson);
        border-color: var(--blodgett-crimson);
      }}

      .btn-crimson:hover,
      .btn-crimson:focus {{
        background: #881726;
        border-color: #881726;
      }}
    </style>
  </head>
  <body>
    <main class="container py-5 py-lg-6">
      <section class="hero rounded-5 p-4 p-md-5 mb-4">
        <div class="row g-4 align-items-center">
          <div class="col-lg-8">
            <p class="hero-tag mb-3">Harvard Recreation scraper</p>
            <h1 class="display-5 fw-semibold mb-3">Blodgett Pool calendar feed</h1>
            <p class="lead mb-0">Subscribe once and your calendar will pick up new Blodgett open swim blocks automatically as this site refreshes.</p>
          </div>
          <div class="col-lg-4">
            <div class="rounded-4 p-4" style="background: rgba(255, 248, 241, 0.12);">
              <div class="small text-uppercase fw-semibold mb-2" style="letter-spacing: 0.08em;">Refresh cadence</div>
              <div class="fs-5 fw-semibold">5am, 1pm, 5pm ET</div>
              <div class="small mt-2 text-white-50">Source: Harvard Recreation facility hours page</div>
            </div>
          </div>
        </div>
      </section>

      <section class="card panel rounded-5 mb-4">
        <div class="card-body p-4 p-lg-5">
          <div class="d-flex flex-column flex-lg-row justify-content-between align-items-lg-center gap-3 mb-4">
            <div>
              <h2 class="h3 mb-1">Subscribe with this feed URL</h2>
              <p class="text-secondary mb-0">Use this ICS URL in Google Calendar, Mac Calendar, or any calendar app that supports subscriptions.</p>
            </div>
            <div class="d-flex gap-2">
              <a class="btn btn-crimson text-white" href="./{ics_name}">Open ICS feed</a>
              <button class="btn btn-outline-dark" id="copy-feed-url" type="button">Copy URL</button>
            </div>
          </div>

          <div class="feed-box rounded-4 p-3 p-md-4">
            <label for="feed-url" class="form-label fw-semibold">Feed URL</label>
            <input id="feed-url" class="form-control form-control-lg feed-input" type="text" readonly value="./{ics_name}">
            <div id="copy-status" class="form-text mt-2">This field will update to the full public URL when the page loads.</div>
          </div>
        </div>
      </section>

      <div class="row g-4">
        <section class="col-lg-6">
          <div class="card panel rounded-5 h-100">
            <div class="card-body p-4 p-lg-5">
              <h2 class="h3 mb-4">Google Calendar</h2>
              <div class="d-flex gap-3 mb-3">
                <span class="step-number flex-shrink-0">1</span>
                <p class="mb-0">Copy the feed URL above.</p>
              </div>
              <div class="d-flex gap-3 mb-3">
                <span class="step-number flex-shrink-0">2</span>
                <p class="mb-0">In Google Calendar on the web, open the plus menu next to <strong>Other calendars</strong>.</p>
              </div>
              <div class="d-flex gap-3 mb-3">
                <span class="step-number flex-shrink-0">3</span>
                <p class="mb-0">Choose <strong>From URL</strong> and paste the feed URL.</p>
              </div>
              <div class="d-flex gap-3">
                <span class="step-number flex-shrink-0">4</span>
                <p class="mb-0">Click <strong>Add calendar</strong>. Google may take a little time to refresh subscribed calendars.</p>
              </div>
            </div>
          </div>
        </section>

        <section class="col-lg-6">
          <div class="card panel rounded-5 h-100">
            <div class="card-body p-4 p-lg-5">
              <h2 class="h3 mb-4">Mac Calendar</h2>
              <div class="d-flex gap-3 mb-3">
                <span class="step-number flex-shrink-0">1</span>
                <p class="mb-0">Copy the feed URL above.</p>
              </div>
              <div class="d-flex gap-3 mb-3">
                <span class="step-number flex-shrink-0">2</span>
                <p class="mb-0">Open the Calendar app and choose <strong>File</strong> then <strong>New Calendar Subscription</strong>.</p>
              </div>
              <div class="d-flex gap-3 mb-3">
                <span class="step-number flex-shrink-0">3</span>
                <p class="mb-0">Paste the feed URL and click <strong>Subscribe</strong>.</p>
              </div>
              <div class="d-flex gap-3">
                <span class="step-number flex-shrink-0">4</span>
                <p class="mb-0">Pick your preferred auto-refresh setting, then save the subscription.</p>
              </div>
            </div>
          </div>
        </section>
      </div>

      <section class="mt-4">
        <div class="card panel rounded-5">
          <div class="card-body p-4 p-lg-5">
            <h2 class="h4 mb-3">What this feed includes</h2>
            <p class="mb-2">Each open Blodgett block becomes its own calendar event. If Harvard adds day-specific notes like lane closures, those notes are attached to each event for that day.</p>
            <p class="text-secondary mb-0">Only the Blodgett Pool entries from the <strong>MAC Pool &amp; Blodgett Pool</strong> table are included.</p>
          </div>
        </div>
      </section>
    </main>

    <script>
      const input = document.getElementById("feed-url");
      const copyButton = document.getElementById("copy-feed-url");
      const copyStatus = document.getElementById("copy-status");
      const feedUrl = new URL("{ics_name}", window.location.href).toString();

      input.value = feedUrl;
      copyStatus.textContent = "Paste this URL into a calendar subscription dialog.";

      copyButton.addEventListener("click", async () => {{
        try {{
          await navigator.clipboard.writeText(feedUrl);
          copyStatus.textContent = "Feed URL copied.";
        }} catch (error) {{
          input.focus();
          input.select();
          copyStatus.textContent = "Copy failed. Select the URL manually and copy it.";
        }}
      }});
    </script>
  </body>
</html>
"""


def format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def escape_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def fold_ical_line(line: str, limit: int = 75) -> str:
    if len(line) <= limit:
        return line

    chunks = [line[index:index + limit] for index in range(0, len(line), limit)]
    return "\r\n ".join(chunks)
