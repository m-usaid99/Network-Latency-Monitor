# tests/test_logger.py

import pytest
from network_latency_monitor.logger import setup_logging


def test_setup_logging_creates_log_file(tmp_path):
    """
    Test that setup_logging creates a log file in the specified directory.
    """
    log_folder = tmp_path / "logs"
    setup_logging(str(log_folder))

    # Check that at least one log file was created
    log_files = list(log_folder.glob("nlm_*.log"))
    assert len(log_files) > 0
    assert log_files[0].is_file()


def test_setup_logging_no_exceptions(tmp_path):
    """
    Test that setup_logging does not raise any exceptions.
    """
    log_folder = tmp_path / "logs"
    try:
        setup_logging(str(log_folder))
    except Exception as e:
        pytest.fail(f"setup_logging raised an exception: {e}")

