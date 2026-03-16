from datetime import datetime
from pathlib import Path

from blodgett_cal.cli import main
from blodgett_cal.parse import ET_ZONE


FIXTURE = Path(__file__).parent / "fixtures" / "facility-hours.html"


def test_build_generates_expected_ics(tmp_path: Path, monkeypatch) -> None:
    import blodgett_cal.cli as cli

    html = FIXTURE.read_text(encoding="utf-8")
    monkeypatch.setattr(cli, "fetch_html", lambda source_url: html)

    exit_code = main(
        [
            "build",
            "--output",
            str(tmp_path),
            "--source-url",
            "https://example.com/facility-hours",
            "--now",
            datetime(2026, 3, 16, 9, 0, tzinfo=ET_ZONE).isoformat(),
        ]
    )

    assert exit_code == 0

    calendar_text = (tmp_path / "blodgett-pool.ics").read_text(encoding="utf-8")
    unfolded_calendar_text = calendar_text.replace("\n ", "")

    assert unfolded_calendar_text.count("BEGIN:VEVENT") == 20
    assert "SUMMARY:Blodgett Pool" in unfolded_calendar_text
    assert "DTSTART:20260316T140000Z" in unfolded_calendar_text
    assert "DTEND:20260316T190000Z" in unfolded_calendar_text
    assert "8 Lane CLOSED 12pm - 1:15pm\\, 7:30pm-9pm" in unfolded_calendar_text
    assert "Source: https://example.com/facility-hours" in unfolded_calendar_text

    index_text = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "./blodgett-pool.ics" in index_text
