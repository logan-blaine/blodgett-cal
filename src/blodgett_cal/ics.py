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
  </head>
  <body>
    <main>
      <h1>Blodgett Pool Calendar Feed</h1>
      <p>Subscribe to the public ICS feed below in Apple Calendar, Google Calendar, Outlook, or any calendar app that supports URL subscriptions.</p>
      <p><a href="./{ics_name}">Open the ICS feed</a></p>
    </main>
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
