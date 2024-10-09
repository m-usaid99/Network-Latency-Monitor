# tests/test_config.py

import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace
from pathlib import Path
import yaml

from network_latency_monitor.config import (
    load_config,
    merge_args_into_config,
    validate_config,
    regenerate_default_config,
    get_standard_directories,
    DEFAULT_CONFIG,
)


def test_get_standard_directories(mocker):
    """
    Test that get_standard_directories returns correct paths based on the mocked AppDirs.
    """
    # Create a mock AppDirs instance with necessary attributes
    mock_appdirs_instance = MagicMock()
    mock_appdirs_instance.user_config_dir = "/mocked/config/dir"
    mock_appdirs_instance.user_data_dir = "/mocked/data/dir"
    mock_appdirs_instance.user_log_dir = "/mocked/log/dir"

    # Patch AppDirs to return the mock instance
    mocker.patch(
        "network_latency_monitor.config.AppDirs", return_value=mock_appdirs_instance
    )

    directories = get_standard_directories("network_latency_monitor")

    assert directories["config_dir"] == Path("/mocked/config/dir")
    assert directories["data_dir"] == Path("/mocked/data/dir")
    assert directories["log_dir"] == Path("/mocked/log/dir")
    assert directories["plots_dir"] == Path("/mocked/data/dir/plots")
    assert directories["results_dir"] == Path("/mocked/data/dir/results")


def test_load_config_existing_valid_config(mocker, tmp_path):
    """
    Test loading an existing valid configuration file.
    """
    # Mock get_standard_directories to use tmp_path
    mock_appdirs_instance = MagicMock()
    mock_appdirs_instance.user_config_dir = str(tmp_path / "config")
    mock_appdirs_instance.user_data_dir = str(tmp_path / "data")
    mock_appdirs_instance.user_log_dir = str(tmp_path / "logs")
    mocker.patch(
        "network_latency_monitor.config.AppDirs", return_value=mock_appdirs_instance
    )

    # Create config.yaml with custom settings
    config_content = {
        "duration": 7200,
        "ip_addresses": ["1.1.1.1", "8.8.4.4"],
        "ping_interval": 2,
        "latency_threshold": 150.0,
        "no_segmentation": True,
    }
    config_file = tmp_path / "config" / "config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with config_file.open("w") as f:
        yaml.safe_dump(config_content, f)

    # Ensure data directories exist
    for dir_path in [
        tmp_path / "data",
        tmp_path / "logs",
        tmp_path / "data" / "plots",
        tmp_path / "data" / "results",
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Patch console to prevent actual printing
    with patch("network_latency_monitor.config.console"):
        config = load_config("config.yaml")

    # Expected config is DEFAULT_CONFIG updated with config_content
    expected_config = {**DEFAULT_CONFIG, **config_content}
    expected_config.update(
        {
            "config_dir": Path(tmp_path / "config"),
            "data_dir": Path(tmp_path / "data"),
            "log_dir": Path(tmp_path / "logs"),
            "plots_dir": Path(tmp_path / "data" / "plots"),
            "results_dir": Path(tmp_path / "data" / "results"),
        }
    )

    # Check that config matches expected_config
    for key in expected_config:
        assert config[key] == expected_config[key], f"Mismatch in key '{key}'"


def test_load_config_missing_config(mocker, tmp_path):
    """
    Test loading configuration when config.yaml does not exist.
    It should create the config file with default settings.
    """
    # Mock get_standard_directories to use tmp_path
    mock_appdirs_instance = MagicMock()
    mock_appdirs_instance.user_config_dir = str(tmp_path / "config")
    mock_appdirs_instance.user_data_dir = str(tmp_path / "data")
    mock_appdirs_instance.user_log_dir = str(tmp_path / "logs")
    mocker.patch(
        "network_latency_monitor.config.AppDirs", return_value=mock_appdirs_instance
    )

    config_file = tmp_path / "config" / "config.yaml"
    # Ensure config.yaml does not exist
    assert not config_file.exists()

    # Ensure data directories do not exist
    for dir_path in [
        tmp_path / "data",
        tmp_path / "logs",
        tmp_path / "data" / "plots",
        tmp_path / "data" / "results",
    ]:
        assert not dir_path.exists()

    # Patch console to prevent actual printing
    with patch("network_latency_monitor.config.console"):
        config = load_config("config.yaml")

    # Expected config is DEFAULT_CONFIG
    expected_config = {**DEFAULT_CONFIG}
    expected_config.update(
        {
            "config_dir": Path(tmp_path / "config"),
            "data_dir": Path(tmp_path / "data"),
            "log_dir": Path(tmp_path / "logs"),
            "plots_dir": Path(tmp_path / "data" / "plots"),
            "results_dir": Path(tmp_path / "data" / "results"),
        }
    )

    # Check that config matches expected_config
    for key in expected_config:
        assert config[key] == expected_config[key], f"Mismatch in key '{key}'"

    # Verify that config.yaml was created with DEFAULT_CONFIG
    assert config_file.exists()
    with config_file.open("r") as f:
        created_config = yaml.safe_load(f)
    assert created_config == DEFAULT_CONFIG

    # Verify that data directories were created
    for dir_path in [
        tmp_path / "data",
        tmp_path / "logs",
        tmp_path / "data" / "plots",
        tmp_path / "data" / "results",
    ]:
        assert dir_path.exists()


def test_load_config_invalid_yaml(mocker, tmp_path):
    """
    Test loading configuration when config.yaml contains invalid YAML.
    It should fallback to default configuration.
    """
    # Mock get_standard_directories to use tmp_path
    mock_appdirs_instance = MagicMock()
    mock_appdirs_instance.user_config_dir = str(tmp_path / "config")
    mock_appdirs_instance.user_data_dir = str(tmp_path / "data")
    mock_appdirs_instance.user_log_dir = str(tmp_path / "logs")
    mocker.patch(
        "network_latency_monitor.config.AppDirs", return_value=mock_appdirs_instance
    )

    # Create config.yaml with invalid YAML
    config_file = tmp_path / "config" / "config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with config_file.open("w") as f:
        f.write(
            "duration: 3600\nip_addresses: [8.8.8.8, 1.1.1.1\n"
        )  # Missing closing bracket

    # Patch console to prevent actual printing
    with patch("network_latency_monitor.config.console"):
        config = load_config("config.yaml")

    # Expected config is DEFAULT_CONFIG with directory paths
    expected_config = {**DEFAULT_CONFIG}
    expected_config.update(
        {
            "config_dir": Path(tmp_path / "config"),
            "data_dir": Path(tmp_path / "data"),
            "log_dir": Path(tmp_path / "logs"),
            "plots_dir": Path(tmp_path / "data" / "plots"),
            "results_dir": Path(tmp_path / "data" / "results"),
        }
    )

    # Check that config matches expected_config
    for key in expected_config:
        assert config[key] == expected_config[key], f"Mismatch in key '{key}'"


def test_merge_args_into_config():
    """
    Test that merge_args_into_config correctly merges CLI arguments into config.
    """
    args = Namespace(
        duration=3600,
        ping_interval=2,
        latency_threshold=150.0,
        no_aggregation=True,
        no_segmentation=True,
        file="results/ping_results.txt",
        clear=True,
        clear_results=False,
        clear_plots=False,
        clear_logs=False,
        yes=True,
        ip_addresses=["8.8.8.8", "1.1.1.1"],
    )

    config = DEFAULT_CONFIG.copy()

    updated_config = merge_args_into_config(args, config)

    assert updated_config["duration"] == 3600
    assert updated_config["ping_interval"] == 2
    assert updated_config["latency_threshold"] == 150.0
    assert updated_config["no_aggregation"] is True
    assert updated_config["no_segmentation"] is True
    assert updated_config["file"] == "results/ping_results.txt"
    assert updated_config["clear"] is True
    assert updated_config["clear_results"] is False
    assert updated_config["clear_plots"] is False
    assert updated_config["clear_logs"] is False
    assert updated_config["yes"] is True
    assert updated_config["ip_addresses"] == ["8.8.8.8", "1.1.1.1"]


def test_validate_config_valid():
    """
    Test that validate_config does not raise an error for valid configurations.
    """
    config = {
        "duration": 3600,
        "ping_interval": 2,
        "latency_threshold": 150.0,
        "ip_addresses": ["8.8.8.8", "1.1.1.1"],
        "no_aggregation": False,
        "no_segmentation": False,
        "file": None,
        "clear": False,
        "clear_results": False,
        "clear_plots": False,
        "clear_logs": False,
        "yes": False,
        "config_dir": Path("/mocked/config/dir"),
        "data_dir": Path("/mocked/data/dir"),
        "log_dir": Path("/mocked/log/dir"),
        "plots_dir": Path("/mocked/data/dir/plots"),
        "results_dir": Path("/mocked/data/dir/results"),
    }

    with patch("network_latency_monitor.config.console"), patch(
        "network_latency_monitor.config.logging"
    ):
        validate_config(config)  # Should not raise


def test_validate_config_invalid_duration():
    """
    Test that validate_config raises SystemExit for invalid duration.
    """
    config = {
        "duration": -100,  # Invalid
        "ping_interval": 2,
        "latency_threshold": 150.0,
        "ip_addresses": ["8.8.8.8"],
        "no_aggregation": False,
        "no_segmentation": False,
        "file": None,
        "clear": False,
        "clear_results": False,
        "clear_plots": False,
        "clear_logs": False,
        "yes": False,
    }

    with patch("network_latency_monitor.config.console"), patch(
        "network_latency_monitor.config.logging"
    ):
        with pytest.raises(SystemExit) as exc_info:
            validate_config(config)
        assert exc_info.value.code == 1


def test_validate_config_invalid_ping_interval():
    """
    Test that validate_config raises SystemExit for invalid ping_interval.
    """
    config = {
        "duration": 3600,
        "ping_interval": 0,  # Invalid
        "latency_threshold": 150.0,
        "ip_addresses": ["8.8.8.8"],
        "no_aggregation": False,
        "no_segmentation": False,
        "file": None,
        "clear": False,
        "clear_results": False,
        "clear_plots": False,
        "clear_logs": False,
        "yes": False,
    }

    with patch("network_latency_monitor.config.console"), patch(
        "network_latency_monitor.config.logging"
    ):
        with pytest.raises(SystemExit) as exc_info:
            validate_config(config)
        assert exc_info.value.code == 1


def test_validate_config_invalid_latency_threshold():
    """
    Test that validate_config raises SystemExit for invalid latency_threshold.
    """
    config = {
        "duration": 3600,
        "ping_interval": 2,
        "latency_threshold": -50.0,  # Invalid
        "ip_addresses": ["8.8.8.8"],
        "no_aggregation": False,
        "no_segmentation": False,
        "file": None,
        "clear": False,
        "clear_results": False,
        "clear_plots": False,
        "clear_logs": False,
        "yes": False,
    }

    with patch("network_latency_monitor.config.console"), patch(
        "network_latency_monitor.config.logging"
    ):
        with pytest.raises(SystemExit) as exc_info:
            validate_config(config)
        assert exc_info.value.code == 1


def test_validate_config_no_ip_addresses():
    """
    Test that validate_config raises SystemExit when no IP addresses are specified.
    """
    config = {
        "duration": 3600,
        "ping_interval": 2,
        "latency_threshold": 150.0,
        "ip_addresses": [],  # Invalid
        "no_aggregation": False,
        "no_segmentation": False,
        "file": None,
        "clear": False,
        "clear_results": False,
        "clear_plots": False,
        "clear_logs": False,
        "yes": False,
    }

    with patch("network_latency_monitor.config.console"), patch(
        "network_latency_monitor.config.logging"
    ):
        with pytest.raises(SystemExit) as exc_info:
            validate_config(config)
        assert exc_info.value.code == 1


def test_regenerate_default_config_existing_confirm_yes(mocker, tmp_path):
    """
    Test regenerating config.yaml when it exists and user confirms regeneration.
    """
    # Mock get_standard_directories to use tmp_path
    mock_appdirs_instance = MagicMock()
    mock_appdirs_instance.user_config_dir = str(tmp_path / "config")
    mock_appdirs_instance.user_data_dir = str(tmp_path / "data")
    mock_appdirs_instance.user_log_dir = str(tmp_path / "logs")
    mocker.patch(
        "network_latency_monitor.config.AppDirs", return_value=mock_appdirs_instance
    )

    # Create existing config.yaml with custom settings
    config_file = tmp_path / "config" / "config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    custom_config = {"duration": 7200}
    with config_file.open("w") as f:
        yaml.safe_dump(custom_config, f)

    # Patch Prompt.ask to return 'y'
    mocker.patch("network_latency_monitor.config.Prompt.ask", return_value="y")

    # Patch console to prevent actual printing
    with patch("network_latency_monitor.config.console"):
        regenerate_default_config("config.yaml")

    # Verify that config.yaml is overwritten with DEFAULT_CONFIG
    with config_file.open("r") as f:
        new_config = yaml.safe_load(f)
    assert new_config == DEFAULT_CONFIG

    # Verify that data directories were created
    for dir_path in [
        tmp_path / "data",
        tmp_path / "logs",
        tmp_path / "data" / "plots",
        tmp_path / "data" / "results",
    ]:
        assert dir_path.exists()


def test_regenerate_default_config_existing_confirm_no(mocker, tmp_path):
    """
    Test regenerating config.yaml when it exists but user declines regeneration.
    """
    # Mock get_standard_directories to use tmp_path
    mock_appdirs_instance = MagicMock()
    mock_appdirs_instance.user_config_dir = str(tmp_path / "config")
    mock_appdirs_instance.user_data_dir = str(tmp_path / "data")
    mock_appdirs_instance.user_log_dir = str(tmp_path / "logs")
    mocker.patch(
        "network_latency_monitor.config.AppDirs", return_value=mock_appdirs_instance
    )

    # Create existing config.yaml with custom settings
    config_file = tmp_path / "config" / "config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    custom_config = {"duration": 7200}
    with config_file.open("w") as f:
        yaml.safe_dump(custom_config, f)

    # Patch Prompt.ask to return 'n'
    mocker.patch("network_latency_monitor.config.Prompt.ask", return_value="n")

    # Patch console to prevent actual printing
    with patch("network_latency_monitor.config.console"):
        regenerate_default_config("config.yaml")

    # Verify that config.yaml is not changed
    with config_file.open("r") as f:
        current_config = yaml.safe_load(f)
    assert current_config == custom_config

    # Verify that data directories were not created (since regeneration didn't proceed)
    for dir_path in [
        tmp_path / "data",
        tmp_path / "logs",
        tmp_path / "data" / "plots",
        tmp_path / "data" / "results",
    ]:
        assert not dir_path.exists()


def test_regenerate_default_config_missing_config(mocker, tmp_path):
    """
    Test regenerating config.yaml when it does not exist.
    It should create the config file with default settings.
    """
    # Mock get_standard_directories to use tmp_path
    mock_appdirs_instance = MagicMock()
    mock_appdirs_instance.user_config_dir = str(tmp_path / "config")
    mock_appdirs_instance.user_data_dir = str(tmp_path / "data")
    mock_appdirs_instance.user_log_dir = str(tmp_path / "logs")
    mocker.patch(
        "network_latency_monitor.config.AppDirs", return_value=mock_appdirs_instance
    )

    config_file = tmp_path / "config" / "config.yaml"
    # Ensure config.yaml does not exist
    assert not config_file.exists()

    # Patch console to prevent actual printing
    with patch("network_latency_monitor.config.console"):
        regenerate_default_config("config.yaml")

    # Verify that config.yaml is created with DEFAULT_CONFIG
    assert config_file.exists()
    with config_file.open("r") as f:
        new_config = yaml.safe_load(f)
    assert new_config == DEFAULT_CONFIG

    # Verify that data directories were created
    for dir_path in [
        tmp_path / "data",
        tmp_path / "logs",
        tmp_path / "data" / "plots",
        tmp_path / "data" / "results",
    ]:
        assert dir_path.exists()


def test_load_config_directory_creation_failure(mocker, tmp_path):
    """
    Test that load_config exits when directory creation fails.
    """
    # Mock get_standard_directories to use tmp_path
    mock_appdirs_instance = MagicMock()
    mock_appdirs_instance.user_config_dir = str(tmp_path / "config")
    mock_appdirs_instance.user_data_dir = str(tmp_path / "data")
    mock_appdirs_instance.user_log_dir = str(tmp_path / "logs")
    mocker.patch(
        "network_latency_monitor.config.AppDirs", return_value=mock_appdirs_instance
    )

    # Simulate directory creation failure by raising an exception
    def mkdir_side_effect(*args, **kwargs):
        raise Exception("Permission denied")

    mocker.patch("pathlib.Path.mkdir", side_effect=mkdir_side_effect)

    # Patch console and sys.exit
    with patch("network_latency_monitor.config.console"), pytest.raises(
        SystemExit
    ) as exc_info:
        load_config("config.yaml")

    # Verify that sys.exit was called with code 1
    assert exc_info.value.code == 1


def test_regenerate_default_config_directory_creation_failure(mocker, tmp_path):
    """
    Test that regenerate_default_config exits when directory creation fails.
    """
    # Mock get_standard_directories to use tmp_path
    mock_appdirs_instance = MagicMock()
    mock_appdirs_instance.user_config_dir = str(tmp_path / "config")
    mock_appdirs_instance.user_data_dir = str(tmp_path / "data")
    mock_appdirs_instance.user_log_dir = str(tmp_path / "logs")
    mocker.patch(
        "network_latency_monitor.config.AppDirs", return_value=mock_appdirs_instance
    )

    # Patch Prompt.ask to return 'y'
    mocker.patch("network_latency_monitor.config.Prompt.ask", return_value="y")

    # Simulate directory creation failure by raising an exception
    def mkdir_side_effect(*args, **kwargs):
        raise Exception("Permission denied")

    mocker.patch("pathlib.Path.mkdir", side_effect=mkdir_side_effect)

    # Patch console and sys.exit
    with patch("network_latency_monitor.config.console"), pytest.raises(
        SystemExit
    ) as exc_info:
        regenerate_default_config("config.yaml")

    # Verify that sys.exit was called with code 1
    assert exc_info.value.code == 1


def test_load_config_yaml_parsing_error(mocker, tmp_path):
    """
    Test that load_config falls back to DEFAULT_CONFIG when YAML parsing fails.
    """
    # Mock get_standard_directories to use tmp_path
    mock_appdirs_instance = MagicMock()
    mock_appdirs_instance.user_config_dir = str(tmp_path / "config")
    mock_appdirs_instance.user_data_dir = str(tmp_path / "data")
    mock_appdirs_instance.user_log_dir = str(tmp_path / "logs")
    mocker.patch(
        "network_latency_monitor.config.AppDirs", return_value=mock_appdirs_instance
    )

    # Create config.yaml with invalid YAML
    config_file = tmp_path / "config" / "config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with config_file.open("w") as f:
        f.write(
            "duration: 3600\nip_addresses: [8.8.8.8, 1.1.1.1\n"
        )  # Missing closing bracket

    # Patch console to prevent actual printing
    with patch("network_latency_monitor.config.console"):
        config = load_config("config.yaml")

    # Expected config is DEFAULT_CONFIG with directory paths
    expected_config = {**DEFAULT_CONFIG}
    expected_config.update(
        {
            "config_dir": Path(tmp_path / "config"),
            "data_dir": Path(tmp_path / "data"),
            "log_dir": Path(tmp_path / "logs"),
            "plots_dir": Path(tmp_path / "data" / "plots"),
            "results_dir": Path(tmp_path / "data" / "results"),
        }
    )

    # Check that config matches expected_config
    for key in expected_config:
        assert config[key] == expected_config[key], f"Mismatch in key '{key}'"


def test_load_config_includes_directories(mocker, tmp_path):
    """
    Test that load_config includes directory paths in the returned config.
    """
    # Mock get_standard_directories to use tmp_path
    mock_appdirs_instance = MagicMock()
    mock_appdirs_instance.user_config_dir = str(tmp_path / "config")
    mock_appdirs_instance.user_data_dir = str(tmp_path / "data")
    mock_appdirs_instance.user_log_dir = str(tmp_path / "logs")
    mocker.patch(
        "network_latency_monitor.config.AppDirs", return_value=mock_appdirs_instance
    )

    # Create config.yaml with some custom settings
    config_content = {
        "duration": 7200,
        "ip_addresses": ["1.1.1.1", "8.8.4.4"],
    }
    config_file = tmp_path / "config" / "config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with config_file.open("w") as f:
        yaml.safe_dump(config_content, f)

    # Ensure data directories exist
    for dir_path in [
        tmp_path / "data",
        tmp_path / "logs",
        tmp_path / "data" / "plots",
        tmp_path / "data" / "results",
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Patch console to prevent actual printing
    with patch("network_latency_monitor.config.console"):
        config = load_config("config.yaml")

    # Expected config is DEFAULT_CONFIG updated with config_content and directory paths
    expected_config = {**DEFAULT_CONFIG, **config_content}
    expected_config.update(
        {
            "config_dir": Path(tmp_path / "config"),
            "data_dir": Path(tmp_path / "data"),
            "log_dir": Path(tmp_path / "logs"),
            "plots_dir": Path(tmp_path / "data" / "plots"),
            "results_dir": Path(tmp_path / "data" / "results"),
        }
    )

    # Check that directory paths are included
    for key in ["config_dir", "data_dir", "log_dir", "plots_dir", "results_dir"]:
        assert config[key] == expected_config[key], f"Mismatch in key '{key}'"

