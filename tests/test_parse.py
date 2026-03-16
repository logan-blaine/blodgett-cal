from datetime import date, datetime
from pathlib import Path

from blodgett_cal.parse import ET_ZONE, infer_dates, parse_blodgett_blocks, parse_time_ranges
from blodgett_cal.scrape import find_pool_accordion, find_pool_table, parse_html


FIXTURE = Path(__file__).parent / "fixtures" / "facility-hours.html"


def load_table():
    soup = parse_html(FIXTURE.read_text(encoding="utf-8"))
    return find_pool_table(find_pool_accordion(soup))


def test_split_hours_into_separate_blocks() -> None:
    ranges = parse_time_ranges("10am-3pm, 5:30pm - 9pm")
    assert [(value[0].isoformat(), value[1].isoformat()) for value in ranges] == [
        ("10:00:00", "15:00:00"),
        ("17:30:00", "21:00:00"),
    ]


def test_closed_rows_generate_no_events() -> None:
    blocks = parse_blodgett_blocks(load_table(), now=datetime(2026, 3, 16, 9, 0, tzinfo=ET_ZONE))
    assert not any(block.source_date_label == "3/14" for block in blocks)


def test_notes_are_copied_to_each_block_for_a_day() -> None:
    blocks = parse_blodgett_blocks(load_table(), now=datetime(2026, 3, 16, 9, 0, tzinfo=ET_ZONE))
    march_16 = [block for block in blocks if block.source_date_label == "3/16"]
    assert len(march_16) == 2
    assert all(block.notes == ("8 Lane CLOSED 12pm - 1:15pm, 7:30pm-9pm",) for block in march_16)


def test_year_inference_rolls_over_december_to_january() -> None:
    inferred = infer_dates([(12, 30), (12, 31), (1, 1), (1, 2)], today=date(2025, 12, 29))
    assert inferred == [
        date(2025, 12, 30),
        date(2025, 12, 31),
        date(2026, 1, 1),
        date(2026, 1, 2),
    ]
