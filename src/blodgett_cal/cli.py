from __future__ import annotations

import argparse
from datetime import datetime
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from .ics import build_calendar, render_index, write_calendar
from .parse import ET_ZONE, parse_blodgett_blocks
from .scrape import DEFAULT_SOURCE_URL, fetch_html, find_pool_accordion, find_pool_table, parse_html

REFRESH_HOURS = {6, 8, 10, 12, 14, 16, 18}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="blodgett-cal")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Scrape the schedule and generate the site output.")
    build.add_argument("--output", type=Path, default=Path("site"))
    build.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    build.add_argument("--now", help="ISO 8601 timestamp used for deterministic builds.")
    build.add_argument(
        "--skip-outside-refresh-window",
        action="store_true",
        help="Exit successfully without rebuilding unless the local ET hour is 6, 8, 10, 12, 14, 16, or 18.",
    )
    build.set_defaults(func=run_build)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def run_build(args: argparse.Namespace) -> int:
    now = parse_now(args.now)
    if args.skip_outside_refresh_window and now.astimezone(ET_ZONE).hour not in REFRESH_HOURS:
        print("REFRESHED=false")
        print("Skipped build outside the ET refresh window.", file=sys.stderr)
        return 0

    html = fetch_html(args.source_url)
    soup = parse_html(html)
    accordion = find_pool_accordion(soup)
    table = find_pool_table(accordion)
    blocks = parse_blodgett_blocks(table, now=now)

    output_dir = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    calendar_text = build_calendar(blocks, source_url=args.source_url, generated_at=now)
    write_calendar(output_dir / "blodgett-pool.ics", calendar_text)
    (output_dir / "index.html").write_text(
        render_index(blocks=blocks, generated_at=now, source_url=args.source_url),
        encoding="utf-8",
    )

    print("REFRESHED=true")
    print(f"Generated {len(blocks)} event(s) in {output_dir / 'blodgett-pool.ics'}", file=sys.stderr)
    return 0


def parse_now(value: str | None) -> datetime:
    if value is None:
        return datetime.now(ZoneInfo("UTC"))

    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ET_ZONE)
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
