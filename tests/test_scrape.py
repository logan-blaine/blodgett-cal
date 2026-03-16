from pathlib import Path

from blodgett_cal.scrape import find_pool_accordion, find_pool_table, parse_html


FIXTURE = Path(__file__).parent / "fixtures" / "facility-hours.html"


def test_selects_pool_accordion_and_blodgett_table_only() -> None:
    soup = parse_html(FIXTURE.read_text(encoding="utf-8"))

    accordion = find_pool_accordion(soup)
    label = accordion.select_one("button span.flex-item-1")
    assert label is not None
    assert "MAC Pool & Blodgett Pool" in label.get_text(" ", strip=True)

    table = find_pool_table(accordion)
    headers = [th.get_text(" ", strip=True) for th in table.select("thead th")]
    assert "Blodgett Pool" in headers
    assert "Murr Pool" not in headers
