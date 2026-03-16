from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha1
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

from .models import PoolBlock

ET_ZONE = ZoneInfo("America/New_York")
DISPLAY_START_HOUR = 6
DISPLAY_END_HOUR = 22
DISPLAY_TOTAL_MINUTES = (DISPLAY_END_HOUR - DISPLAY_START_HOUR) * 60


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


def render_index(
    blocks: list[PoolBlock] | None = None,
    generated_at: datetime | None = None,
    ics_name: str = "blodgett-pool.ics",
    source_url: str = "",
) -> str:
    blocks = blocks or []
    generated_at = (generated_at or datetime.now(timezone.utc)).astimezone(ET_ZONE)
    source_link = source_url or "#"
    week_overview = render_week_overview(blocks, generated_at)
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

      .week-grid {{
        display: grid;
        grid-template-columns: repeat(7, minmax(0, 1fr));
        gap: 1rem;
      }}

      .day-card {{
        border: 1px solid rgba(165, 28, 48, 0.08);
        border-radius: 1.5rem;
        background: rgba(255, 255, 255, 0.9);
        overflow: hidden;
      }}

      .day-card.today {{
        box-shadow: inset 0 0 0 2px rgba(165, 28, 48, 0.25);
      }}

      .day-heading {{
        border-bottom: 1px solid rgba(29, 27, 26, 0.08);
        background: linear-gradient(180deg, rgba(165, 28, 48, 0.05), rgba(165, 28, 48, 0));
      }}

      .timeline {{
        position: relative;
        height: 32rem;
        background-image:
          repeating-linear-gradient(
            to bottom,
            rgba(29, 27, 26, 0.05) 0,
            rgba(29, 27, 26, 0.05) 1px,
            transparent 1px,
            transparent 12.5%
          );
      }}

      .time-markers {{
        position: absolute;
        inset: 0 auto 0 0;
        width: 3rem;
        border-right: 1px solid rgba(29, 27, 26, 0.08);
        background: rgba(246, 240, 232, 0.55);
      }}

      .time-marker {{
        position: absolute;
        left: 0.45rem;
        transform: translateY(-50%);
        font-size: 0.72rem;
        color: rgba(29, 27, 26, 0.62);
      }}

      .day-lane {{
        position: absolute;
        inset: 0 0 0 3rem;
        padding: 0.65rem;
      }}

      .block-chip {{
        position: absolute;
        left: 0.65rem;
        right: 0.65rem;
        border-radius: 1rem;
        padding: 0.55rem 0.6rem;
        background: linear-gradient(180deg, rgba(165, 28, 48, 0.92), rgba(132, 21, 38, 0.96));
        color: #fff8f1;
        box-shadow: 0 10px 22px rgba(101, 18, 31, 0.22);
        overflow: hidden;
      }}

      .block-chip.has-notes {{
        background: linear-gradient(180deg, rgba(165, 28, 48, 0.92), rgba(108, 34, 66, 0.96));
      }}

      .block-time {{
        font-size: 0.84rem;
        font-weight: 700;
        line-height: 1.15;
      }}

      .block-note {{
        font-size: 0.72rem;
        opacity: 0.9;
        margin-top: 0.3rem;
        line-height: 1.2;
      }}

      .day-empty {{
        position: absolute;
        inset: 0 0 0 3rem;
        display: flex;
        align-items: center;
        justify-content: center;
        color: rgba(29, 27, 26, 0.55);
        font-size: 0.9rem;
        text-align: center;
        padding: 1rem;
      }}

      @media (max-width: 1200px) {{
        .week-grid {{
          grid-template-columns: repeat(4, minmax(0, 1fr));
        }}
      }}

      @media (max-width: 992px) {{
        .week-grid {{
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
      }}

      @media (max-width: 576px) {{
        .week-grid {{
          grid-template-columns: 1fr;
        }}

        .timeline {{
          height: 24rem;
        }}
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
              <div class="small mt-2">
                <a class="link-light link-underline-opacity-50 link-underline-opacity-100-hover" href="{source_link}">View the Harvard Recreation source page</a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {week_overview}

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
            <p class="text-secondary mb-2">Only the Blodgett Pool entries from the <strong>MAC Pool &amp; Blodgett Pool</strong> table are included.</p>
            <p class="mb-0"><a href="{source_link}">Open the current Harvard Recreation schedule page</a></p>
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


def render_week_overview(blocks: list[PoolBlock], generated_at: datetime) -> str:
    week_dates = current_week_dates(generated_at)
    start_date = week_dates[0]
    end_date = week_dates[-1]
    blocks_by_date: dict[datetime.date, list[PoolBlock]] = defaultdict(list)
    for block in blocks:
        blocks_by_date[block.date_local].append(block)

    day_columns = "\n".join(
        render_day_column(day_date, sorted(blocks_by_date.get(day_date, []), key=lambda block: block.start_local), generated_at)
        for day_date in week_dates
    )

    return f"""
      <section class="card panel rounded-5 mb-4">
        <div class="card-body p-4 p-lg-5">
          <div class="d-flex flex-column flex-lg-row justify-content-between align-items-lg-end gap-3 mb-4">
            <div>
              <h2 class="h3 mb-1">This Week at a Glance</h2>
              <p class="text-secondary mb-0">{escape(format_date_range(start_date, end_date))} · Times shown in ET.</p>
            </div>
            <div class="small text-secondary">Blocks shown here are pulled from the latest published Harvard schedule snapshot.</div>
          </div>
          <div class="week-grid">
            {day_columns}
          </div>
        </div>
      </section>
"""


def render_day_column(day_date, day_blocks: list[PoolBlock], generated_at: datetime) -> str:
    day_name = day_date.strftime("%a")
    day_label = day_date.strftime("%b %-d")
    is_today = day_date == generated_at.date()
    card_class = "day-card today" if is_today else "day-card"
    blocks_html = "\n".join(render_block_chip(block) for block in day_blocks)
    if not blocks_html:
        blocks_html = '<div class="day-empty">No published block</div>'

    return f"""
            <article class="{card_class}">
              <div class="day-heading p-3">
                <div class="d-flex justify-content-between align-items-baseline gap-2">
                  <h3 class="h5 mb-0">{escape(day_name)}</h3>
                  <span class="text-secondary small">{escape(day_label)}</span>
                </div>
              </div>
              <div class="timeline">
                <div class="time-markers">
                  {render_time_markers()}
                </div>
                <div class="day-lane">
                  {blocks_html}
                </div>
              </div>
            </article>
"""


def render_time_markers() -> str:
    markers = []
    for hour in range(DISPLAY_START_HOUR, DISPLAY_END_HOUR + 1, 2):
        top_pct = ((hour - DISPLAY_START_HOUR) * 60 / DISPLAY_TOTAL_MINUTES) * 100
        markers.append(
            f'<span class="time-marker" style="top: {top_pct:.3f}%;">{escape(format_hour_label(hour))}</span>'
        )
    return "".join(markers)


def render_block_chip(block: PoolBlock) -> str:
    start_minutes = block.start_local.hour * 60 + block.start_local.minute
    end_minutes = block.end_local.hour * 60 + block.end_local.minute
    top_pct = ((start_minutes - DISPLAY_START_HOUR * 60) / DISPLAY_TOTAL_MINUTES) * 100
    height_pct = ((end_minutes - start_minutes) / DISPLAY_TOTAL_MINUTES) * 100
    top_pct = max(0.0, min(100.0, top_pct))
    height_pct = max(6.0, min(100.0 - top_pct, height_pct))
    notes_text = " | ".join(block.notes)
    note_html = ""
    extra_class = ""
    title_attr = ""
    if notes_text:
        extra_class = " has-notes"
        note_html = f'<div class="block-note">{escape(truncate_note(notes_text))}</div>'
        title_attr = f' title="{escape(notes_text, quote=True)}"'

    return f"""
                  <div class="block-chip{extra_class}" style="top: {top_pct:.3f}%; height: {height_pct:.3f}%;"{title_attr}>
                    <div class="block-time">{escape(format_time_display(block.start_local, block.end_local))}</div>
                    {note_html}
                  </div>
"""


def current_week_dates(generated_at: datetime) -> list:
    start_date = generated_at.date()
    monday = start_date.fromordinal(start_date.toordinal() - start_date.weekday())
    return [monday.fromordinal(monday.toordinal() + offset) for offset in range(7)]


def format_date_range(start_date, end_date) -> str:
    if start_date.month == end_date.month:
        return f"{start_date.strftime('%b')} {start_date.day} - {end_date.day}"
    return f"{start_date.strftime('%b')} {start_date.day} - {end_date.strftime('%b')} {end_date.day}"


def format_hour_label(hour: int) -> str:
    suffix = "am" if hour < 12 else "pm"
    display_hour = hour if 1 <= hour <= 12 else hour - 12
    if display_hour == 0:
        display_hour = 12
    return f"{display_hour}{suffix}"


def format_time_display(start_local, end_local) -> str:
    return f"{format_single_time(start_local)} - {format_single_time(end_local)}"


def format_single_time(value) -> str:
    hour = value.hour
    minute = value.minute
    suffix = "am" if hour < 12 else "pm"
    display_hour = hour % 12 or 12
    if minute == 0:
        return f"{display_hour}{suffix}"
    return f"{display_hour}:{minute:02d}{suffix}"


def truncate_note(note: str, limit: int = 42) -> str:
    if len(note) <= limit:
        return note
    return note[: limit - 1].rstrip() + "…"


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
