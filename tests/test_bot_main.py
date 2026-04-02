"""Tests for bot presentation helpers."""

from __future__ import annotations

from apps.bot.main import build_pagination_keyboard


def test_build_pagination_keyboard_hides_next_on_last_page() -> None:
    keyboard = build_pagination_keyboard(
        {
            "hits": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}],
            "estimatedTotalHits": 5,
        },
        page=0,
    )

    assert keyboard is None


def test_build_pagination_keyboard_shows_next_when_more_results_exist() -> None:
    keyboard = build_pagination_keyboard(
        {
            "hits": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}],
            "estimatedTotalHits": 11,
        },
        page=0,
    )

    assert keyboard is not None
    assert keyboard.inline_keyboard[0][0].callback_data == "next"
