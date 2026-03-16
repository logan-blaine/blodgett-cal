from datetime import date, datetime, time

from blodgett_cal.ics import ET_ZONE, render_index
from blodgett_cal.models import PoolBlock


def test_render_index_includes_subscription_instructions() -> None:
    html = render_index(
        blocks=[
            PoolBlock(
                date_local=date(2026, 3, 16),
                start_local=time(10, 0),
                end_local=time(15, 0),
                notes=("8 Lane CLOSED 12pm - 1:15pm",),
                source_day_label="Monday",
                source_date_label="3/16",
            )
        ],
        generated_at=datetime(2026, 3, 16, 9, 0, tzinfo=ET_ZONE),
        source_url="https://example.com/source",
    )

    assert "Google Calendar" in html
    assert "Mac Calendar" in html
    assert "Copy URL" in html
    assert "blodgett-pool.ics" in html
    assert "https://example.com/source" in html
    assert "This Week at a Glance" in html
    assert "10am - 3pm" in html
    assert "8 Lane CLOSED 12pm - 1:15pm" in html
