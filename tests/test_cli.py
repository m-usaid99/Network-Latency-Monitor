# tests/test_cli.py

import pytest
from network_latency_monitor.cli import parse_arguments


def test_parse_arguments_no_args(monkeypatch):
    """
    Test parsing with no arguments. Should use default values.
    """
    test_args = ["nlm"]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_arguments()

    assert args.ip_addresses == []
    assert args.duration == 10800
    assert args.ping_interval == 1
    assert args.file is None
    assert args.latency_threshold == 200.0
    assert not args.no_segmentation
    assert not args.regen_config
    assert not args.no_aggregation
    assert not args.clear
    assert not args.clear_results
    assert not args.clear_plots
    assert not args.clear_logs
    assert not args.yes


def test_parse_arguments_with_ips(monkeypatch):
    """
    Test parsing with positional IP addresses.
    """
    test_args = ["nlm", "8.8.8.8", "1.1.1.1"]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_arguments()

    assert args.ip_addresses == ["8.8.8.8", "1.1.1.1"]
    # Defaults for other arguments
    assert args.duration == 10800
    assert args.ping_interval == 1
    assert args.file is None
    assert args.latency_threshold == 200.0
    assert not args.no_segmentation
    assert not args.regen_config
    assert not args.no_aggregation
    assert not args.clear
    assert not args.clear_results
    assert not args.clear_plots
    assert not args.clear_logs
    assert not args.yes


def test_parse_arguments_custom_options(monkeypatch):
    """
    Test parsing with various custom options.
    """
    test_args = [
        "nlm",
        "8.8.8.8",
        "--duration",
        "3600",
        "--ping-interval",
        "2",
        "--latency-threshold",
        "150.0",
        "--no-segmentation",
        "--regen-config",
        "--no-aggregation",
        "--yes",
    ]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_arguments()

    assert args.ip_addresses == ["8.8.8.8"]
    assert args.duration == 3600
    assert args.ping_interval == 2
    assert args.latency_threshold == 150.0
    assert args.no_segmentation
    assert args.regen_config
    assert args.no_aggregation
    assert not args.clear
    assert not args.clear_results
    assert not args.clear_plots
    assert not args.clear_logs
    assert args.yes


def test_parse_arguments_clear_all(monkeypatch):
    """
    Test parsing the --clear flag.
    """
    test_args = ["nlm", "--clear"]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_arguments()

    assert args.clear
    assert not args.clear_results
    assert not args.clear_plots
    assert not args.clear_logs
    # Other defaults
    assert args.ip_addresses == []
    assert args.duration == 10800
    assert args.ping_interval == 1
    assert args.file is None
    assert args.latency_threshold == 200.0
    assert not args.no_segmentation
    assert not args.regen_config
    assert not args.no_aggregation
    assert not args.yes


def test_parse_arguments_clear_results(monkeypatch):
    """
    Test parsing the --clear-results flag.
    """
    test_args = ["nlm", "--clear-results"]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_arguments()

    assert not args.clear
    assert args.clear_results
    assert not args.clear_plots
    assert not args.clear_logs
    # Other defaults
    assert args.ip_addresses == []
    assert args.duration == 10800
    assert args.ping_interval == 1
    assert args.file is None
    assert args.latency_threshold == 200.0
    assert not args.no_segmentation
    assert not args.regen_config
    assert not args.no_aggregation
    assert not args.yes


def test_parse_arguments_mutually_exclusive_clear(monkeypatch):
    """
    Test that mutually exclusive clear options work correctly.
    Only one clear option should be True at a time.
    """
    test_args = ["nlm", "--clear-plots", "--clear-results"]
    monkeypatch.setattr("sys.argv", test_args)

    with pytest.raises(SystemExit) as exc_info:
        parse_arguments()

    assert exc_info.value.code == 2  # argparse exits with code 2 on error


def test_parse_arguments_help(monkeypatch):
    """
    Test that --help displays the help message and exits.
    """
    test_args = ["nlm", "--help"]
    monkeypatch.setattr("sys.argv", test_args)

    with pytest.raises(SystemExit) as exc_info:
        parse_arguments()

    assert exc_info.value.code == 0  # argparse exits with code 0 on help


def test_parse_arguments_file_option(monkeypatch):
    """
    Test parsing the --file option.
    """
    test_args = ["nlm", "--file", "results/ping_results.txt"]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_arguments()

    assert args.file == "results/ping_results.txt"
    # Other defaults
    assert args.ip_addresses == []
    assert args.duration == 10800
    assert args.ping_interval == 1
    assert args.latency_threshold == 200.0
    assert not args.no_segmentation
    assert not args.regen_config
    assert not args.no_aggregation
    assert not args.clear
    assert not args.clear_results
    assert not args.clear_plots
    assert not args.clear_logs
    assert not args.yes
