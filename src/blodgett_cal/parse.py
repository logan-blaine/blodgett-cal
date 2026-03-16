from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time
import re
from zoneinfo import ZoneInfo

from bs4 import Tag

from .models import PoolBlock

ET_ZONE = ZoneInfo("America/New_York")
MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
TIME_TOKEN_RE = re.compile(
    r"^\s*(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<meridiem>am|pm)?\s*$",
    re.IGNORECASE,
)
RANGE_RE = re.compile(r"^\s*(?P<start>.+?)\s*-\s*(?P<end>.+?)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedCell:
    hours_text: str
    notes: tuple[str, ...]


def parse_blodgett_blocks(table: Tag, now: datetime | None = None) -> list[PoolBlock]:
    now_et = (now or datetime.now(ET_ZONE)).astimezone(ET_ZONE)
    rows = table.select("tbody tr")
    if not rows:
        return []

    headers = [normalize_text(th.get_text(" ", strip=True)) for th in table.select("thead th")]
    blodgett_index = _find_index(headers, "blodgett pool")
    date_index = _find_index(headers, "date", default=0)
    day_index = _find_index(headers, "day", default=1 if blodgett_index >= 3 else None)

    row_data: list[tuple[str, str, ParsedCell]] = []
    month_days: list[tuple[int, int]] = []

    for row in rows:
        cells = row.find_all(["td", "th"], recursive=False)
        if len(cells) <= blodgett_index:
            continue

        source_date_label = normalize_cell_text(cells[date_index]) if date_index is not None else ""
        source_day_label = normalize_cell_text(cells[day_index]) if day_index is not None else ""
        parsed_cell = extract_cell_runs(cells[blodgett_index])
        row_data.append((source_date_label, source_day_label, parsed_cell))
        month_days.append(parse_month_day(source_date_label))

    inferred_dates = infer_dates(month_days, now_et.date())
    blocks: list[PoolBlock] = []

    for (source_date_label, source_day_label, parsed_cell), local_date in zip(row_data, inferred_dates):
        if is_closed(parsed_cell.hours_text):
            continue
        for start_local, end_local in parse_time_ranges(parsed_cell.hours_text):
            blocks.append(
                PoolBlock(
                    date_local=local_date,
                    start_local=start_local,
                    end_local=end_local,
                    notes=parsed_cell.notes,
                    source_day_label=source_day_label,
                    source_date_label=source_date_label,
                )
            )

    return blocks


def normalize_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = value.replace("–", "-").replace("—", "-").replace("−", "-")
    return " ".join(value.split()).strip()


def normalize_cell_text(cell: Tag) -> str:
    return normalize_text(cell.get_text(" ", strip=True))


def extract_cell_runs(cell: Tag) -> ParsedCell:
    blocks = []
    for child in cell.children:
        if isinstance(child, str):
            text = normalize_text(child)
            if text:
                blocks.append(text)
            continue
        if not isinstance(child, Tag):
            continue
        text = normalize_text(child.get_text(" ", strip=True))
        if text:
            blocks.append(text)

    if not blocks:
        full_text = normalize_cell_text(cell)
        blocks = [full_text] if full_text else []

    if not blocks:
        return ParsedCell(hours_text="", notes=())

    return ParsedCell(hours_text=blocks[0], notes=tuple(blocks[1:]))


def parse_month_day(label: str) -> tuple[int, int]:
    text = normalize_text(label).lower()
    if not text:
        raise ValueError("Missing source date label")

    slash_match = re.match(r"(?P<month>\d{1,2})/(?P<day>\d{1,2})(?:/(?P<year>\d{4}))?$", text)
    if slash_match:
        return int(slash_match.group("month")), int(slash_match.group("day"))

    words = text.replace(",", "").split()
    if len(words) >= 2 and words[0] in MONTHS:
        return MONTHS[words[0]], int(words[1])

    raise ValueError(f"Unsupported date label: {label!r}")


def infer_dates(month_days: Iterable[tuple[int, int]], today: date) -> list[date]:
    month_days_list = list(month_days)
    if not month_days_list:
        return []

    first_month, first_day = month_days_list[0]
    candidate_years = [today.year - 1, today.year, today.year + 1]
    starting_year = min(
        candidate_years,
        key=lambda year: abs((date(year, first_month, first_day) - today).days),
    )

    inferred: list[date] = []
    current_year = starting_year
    previous_month_day: tuple[int, int] | None = None

    for month, day in month_days_list:
        if previous_month_day and (month, day) < previous_month_day:
            current_year += 1
        inferred.append(date(current_year, month, day))
        previous_month_day = (month, day)

    return inferred


def is_closed(hours_text: str) -> bool:
    return normalize_text(hours_text).lower() == "closed"


def parse_time_ranges(hours_text: str) -> list[tuple[time, time]]:
    normalized = normalize_text(hours_text).replace("/", ",").replace(";", ",")
    segments = [segment.strip() for segment in normalized.split(",") if segment.strip()]
    ranges: list[tuple[time, time]] = []

    for segment in segments:
        match = RANGE_RE.match(segment)
        if match is None:
            raise ValueError(f"Unsupported time range segment: {segment!r}")
        ranges.append(parse_single_range(match.group("start"), match.group("end")))

    return ranges


def parse_single_range(start_text: str, end_text: str) -> tuple[time, time]:
    start_candidates = time_candidates(start_text)
    end_candidates = time_candidates(end_text)
    best: tuple[int, tuple[time, time]] | None = None

    for start_time in start_candidates:
        for end_time in end_candidates:
            start_minutes = to_minutes(start_time)
            end_minutes = to_minutes(end_time)
            duration = end_minutes - start_minutes
            if duration <= 0 or duration > 16 * 60:
                continue
            if best is None or duration < best[0]:
                best = (duration, (start_time, end_time))

    if best is None:
        raise ValueError(f"Could not parse time range {start_text!r} - {end_text!r}")

    return best[1]


def time_candidates(text: str) -> list[time]:
    cleaned = normalize_text(text).lower().replace(" ", "")
    match = TIME_TOKEN_RE.match(cleaned)
    if match is None:
        raise ValueError(f"Unsupported time token: {text!r}")

    hour = int(match.group("hour"))
    minute = int(match.group("minute") or 0)
    meridiem = match.group("meridiem")

    meridiems = [meridiem] if meridiem else ["am", "pm"]
    return [time(to_24_hour(hour, minute, value), minute) for value in meridiems]


def to_24_hour(hour: int, minute: int, meridiem: str) -> int:
    if hour < 1 or hour > 12:
        raise ValueError(f"Hour out of range: {hour}")
    hour_24 = hour % 12
    if meridiem == "pm":
        hour_24 += 12
    return hour_24


def to_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def _find_index(headers: list[str], target: str, default: int | None = None) -> int | None:
    normalized_target = normalize_text(target).lower()
    for index, header in enumerate(headers):
        if normalize_text(header).lower() == normalized_target:
            return index
    return default
