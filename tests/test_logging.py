"""Tests for telegram_search.logging."""

from __future__ import annotations

from telegram_search.logging import get_logger, safe_error, setup_logging


class TestSetupLogging:
    def test_setup_logging_debug_false(self) -> None:
        setup_logging(debug=False)

    def test_setup_logging_debug_true(self) -> None:
        setup_logging(debug=True)


class TestGetLogger:
    def test_returns_bound_logger(self) -> None:
        setup_logging()
        logger = get_logger("test")
        assert type(logger).__name__ == "BoundLoggerLazyProxy"


class TestSafeError:
    def test_plain_exception(self) -> None:
        err = Exception("boom")
        result = safe_error(err)
        assert result == {"error_type": "Exception"}

    def test_status_code_included(self) -> None:
        err = RuntimeError("fail")
        err.status_code = 500  # type: ignore[attr-defined]
        result = safe_error(err)
        assert result["error_type"] == "RuntimeError"
        assert result["status_code"] == 500

    def test_code_included(self) -> None:
        err = ValueError("bad")
        err.code = 42  # type: ignore[attr-defined]
        result = safe_error(err)
        assert result["error_type"] == "ValueError"
        assert result["code"] == 42

    def test_errno_included(self) -> None:
        err = OSError("no file")
        err.errno = 2
        result = safe_error(err)
        assert result["error_type"] == "OSError"
        assert result["errno"] == 2

    def test_missing_attributes_excluded(self) -> None:
        err = Exception("plain")
        result = safe_error(err)
        assert "status_code" not in result
        assert "code" not in result
        assert "errno" not in result
