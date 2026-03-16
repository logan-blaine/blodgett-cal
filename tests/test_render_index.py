from blodgett_cal.ics import render_index


def test_render_index_includes_subscription_instructions() -> None:
    html = render_index()

    assert "Google Calendar" in html
    assert "Mac Calendar" in html
    assert "Copy URL" in html
    assert "blodgett-pool.ics" in html
