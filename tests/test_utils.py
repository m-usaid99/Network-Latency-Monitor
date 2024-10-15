# # tests/test_utils.py
#
# import pytest
# import sys
# from pathlib import Path
# from unittest.mock import patch, MagicMock
# from typing import Dict, List
# from datetime import datetime
#
# from network_latency_monitor.utils import (
#     clear_data,
#     ask_confirmation,
#     handle_clear_operations,
#     validate_and_get_ips,
#     create_results_directory,
# )
#
# # 1. clear_data Tests
#
#
# def test_clear_data(tmp_path):
#     # Create temporary directories
#     dir1 = tmp_path / "dir1"
#     dir2 = tmp_path / "dir2"
#     dir1.mkdir()
#     dir2.mkdir()
#
#     assert dir1.exists()
#     assert dir2.exists()
#
#     # Call clear_data
#     clear_data([dir1, dir2])
#
#     # Verify directories are deleted
#     assert not dir1.exists()
#     assert not dir2.exists()
#
#
# def test_clear_data_folder_not_found(tmp_path, caplog):
#     # Create a temporary directory and then remove it to simulate "not found"
#     dir1 = tmp_path / "dir1"
#     dir1.mkdir()
#     dir1.rmdir()
#     # Verify that a warning was logged
#     assert any("Folder not found" in message for message in caplog.text.splitlines())
#
#
# def test_clear_data_permission_error(tmp_path):
#     # Create a temporary directory and make it read-only
#     dir1 = tmp_path / "dir1"
#     dir1.mkdir()
#     dir1.chmod(0o400)  # Read-only
#
#     with patch("shutil.rmtree", side_effect=OSError("Permission denied")):
#         with pytest.raises(OSError, match="Permission denied"):
#             clear_data([dir1])
#
#
# # 2. ask_confirmation Tests
#
#
# def test_ask_confirmation_auto_confirm_true():
#     result = ask_confirmation("Are you sure?", auto_confirm=True)
#     assert result is True
#
#
# @patch("network_latency_monitor.utils.Prompt.ask")
# def test_ask_confirmation_user_yes(mock_ask):
#     mock_ask.return_value = "y"
#     result = ask_confirmation("Are you sure?", auto_confirm=False)
#     assert result is True
#     mock_ask.assert_called_once_with("Are you sure?", choices=["y", "n"], default="n")
#
#
# @patch("network_latency_monitor.utils.Prompt.ask")
# def test_ask_confirmation_user_no(mock_ask):
#     mock_ask.return_value = "n"
#     result = ask_confirmation("Are you sure?", auto_confirm=False)
#     assert result is False
#     mock_ask.assert_called_once_with("Are you sure?", choices=["y", "n"], default="n")
#
#
# # 3. handle_clear_operations Tests
#
#
# @patch("network_latency_monitor.utils.clear_data")
# @patch("network_latency_monitor.utils.ask_confirmation")
# @patch("network_latency_monitor.utils.sys.exit")  # Patch sys.exit here
# def test_handle_clear_operations_clear_all_true(
#     mock_exit, mock_ask, mock_clear_data, tmp_path
# ):
#     config: Dict = {
#         "clear": True,
#         "results_dir": tmp_path / "results",
#         "plots_dir": tmp_path / "plots",
#         "log_dir": tmp_path / "logs",
#         "yes": True,
#     }
#
#     # Create directories
#     config["results_dir"].mkdir()
#     config["plots_dir"].mkdir()
#     config["log_dir"].mkdir()
#
#     # Call handle_clear_operations
#     handle_clear_operations(config)
#
#     # Verify that clear_data was called with all directories
#     mock_clear_data.assert_called_once_with(
#         [config["results_dir"], config["plots_dir"], config["log_dir"]]
#     )
#
#     # Verify that sys.exit was called with 0
#     mock_exit.assert_called_once_with(0)
#
#
# @patch("network_latency_monitor.utils.clear_data")
# @patch("network_latency_monitor.utils.ask_confirmation")
# @patch("network_latency_monitor.utils.sys.exit")  # Patch sys.exit here
# def test_handle_clear_operations_partial_clear(
#     mock_exit, mock_ask, mock_clear_data, tmp_path
# ):
#     config: Dict = {
#         "clear": False,
#         "clear_results": True,
#         "clear_plots": False,
#         "clear_logs": True,
#         "results_dir": tmp_path / "results",
#         "plots_dir": tmp_path / "plots",
#         "log_dir": tmp_path / "logs",
#         "yes": False,
#     }
#
#     # Create directories
#     config["results_dir"].mkdir()
#     config["log_dir"].mkdir()
#
#     mock_ask.return_value = True
#
#     # Call handle_clear_operations
#     handle_clear_operations(config)
#
#     # Verify that clear_data was called with selected directories
#     mock_clear_data.assert_called_once_with([config["results_dir"], config["log_dir"]])
#
#     # Verify that sys.exit was called with 0
#     mock_exit.assert_called_once_with(0)
#
#
# @patch("network_latency_monitor.utils.clear_data")
# @patch("network_latency_monitor.utils.ask_confirmation", return_value=False)
# @patch("network_latency_monitor.utils.sys.exit")  # Patch sys.exit here
# def test_handle_clear_operations_cancel(mock_exit, mock_ask, mock_clear_data, tmp_path):
#     config: Dict = {
#         "clear": True,
#         "results_dir": tmp_path / "results",
#         "plots_dir": tmp_path / "plots",
#         "log_dir": tmp_path / "logs",
#         "yes": False,
#     }
#
#     # Create directories
#     config["results_dir"].mkdir()
#     config["plots_dir"].mkdir()
#     config["log_dir"].mkdir()
#
#     # Call handle_clear_operations
#     handle_clear_operations(config)
#
#     # Verify that clear_data was NOT called
#     mock_clear_data.assert_not_called()
#
#     # Verify that sys.exit was called with 0
#     mock_exit.assert_called_once_with(0)
#
#
# # 4. validate_and_get_ips Tests
#
#
# @patch("network_latency_monitor.utils.console")
# def test_validate_and_get_ips_all_valid(mock_console, tmp_path):
#     config: Dict = {"ip_addresses": ["8.8.8.8", "1.1.1.1"]}
#
#     result = validate_and_get_ips(config)
#     assert result == ["8.8.8.8", "1.1.1.1"]
#
#
# @patch("network_latency_monitor.utils.console")
# @patch("network_latency_monitor.utils.logging")
# def test_validate_and_get_ips_some_invalid(mock_logging, mock_console, tmp_path):
#     config: Dict = {"ip_addresses": ["8.8.8.8", "invalid_ip", "1.1.1.1"]}
#
#     result = validate_and_get_ips(config)
#     assert result == ["8.8.8.8", "1.1.1.1"]
#     mock_console.print.assert_any_call(
#         "[bold red]Invalid IP address:[/bold red] invalid_ip"
#     )
#     mock_logging.error.assert_called_with("Invalid IP address provided: invalid_ip")
#
#
# @patch("network_latency_monitor.utils.console")
# @patch("network_latency_monitor.utils.logging")
# def test_validate_and_get_ips_all_invalid(mock_logging, mock_console, tmp_path):
#     config: Dict = {"ip_addresses": ["invalid_ip1", "invalid_ip2"]}
#
#     with patch("network_latency_monitor.utils.sys.exit") as mock_exit:
#         validate_and_get_ips(config)
#         mock_console.print.assert_any_call(
#             "[bold red]Invalid IP address:[/bold red] invalid_ip1"
#         )
#         mock_console.print.assert_any_call(
#             "[bold red]Invalid IP address:[/bold red] invalid_ip2"
#         )
#         mock_console.print.assert_any_call(
#             "[bold red]No valid IP addresses provided. Exiting.[/bold red]"
#         )
#         mock_logging.error.assert_called_with(
#             "No valid IP addresses provided. Exiting."
#         )
#         mock_exit.assert_called_once_with(1)
#
#
# # 5. create_results_directory Tests
#
#
# @patch("network_latency_monitor.utils.console")
# @patch("network_latency_monitor.utils.logging")
# def test_create_results_directory_success(mock_logging, mock_console, tmp_path):
#     config: Dict = {"results_dir": tmp_path / "results"}
#     config["results_dir"].mkdir()
#
#     # Create a fixed datetime object
#     fixed_datetime = datetime(2024, 10, 9, 15, 33, 23)
#
#     with patch("network_latency_monitor.utils.datetime") as mock_datetime:
#         mock_datetime.now.return_value = fixed_datetime
#         # Mock strftime to return the desired format
#         mock_datetime.now.strftime.return_value = "2024-10-09_15-33-23"
#
#         # Call create_results_directory
#         create_results_directory(config)
#
#         # Define the expected subfolder path
#         expected_subfolder = config["results_dir"] / "results_2024-10-09_15-33-23"
#
#         # Verify that the subfolder was created
#         assert expected_subfolder.exists()
#
#         # Verify that console.print was called with the correct message
#         mock_console.print.assert_called_with(
#             f"[bold green]Created results subdirectory:[/bold green] {expected_subfolder}"
#         )
#
#
# @patch("network_latency_monitor.utils.console")
# @patch("network_latency_monitor.utils.logging")
# def test_create_results_directory_creation_failure(
#     mock_logging, mock_console, tmp_path
# ):
#     config: Dict = {"results_dir": tmp_path / "results"}
#     config["results_dir"].mkdir()
#
#     # Create a fixed datetime object
#     fixed_datetime = datetime(2024, 10, 9, 15, 33, 23)
#
#     with patch("network_latency_monitor.utils.datetime") as mock_datetime:
#         mock_datetime.now.return_value = fixed_datetime
#         # Mock strftime to return the desired format
#         mock_datetime.now.strftime.return_value = "2024-10-09_15-33-23"
#
#         with patch(
#             "network_latency_monitor.utils.Path.mkdir",
#             side_effect=OSError("Permission denied"),
#         ):
#             with patch("network_latency_monitor.utils.sys.exit") as mock_exit:
#                 # Call create_results_directory
#                 create_results_directory(config)
#
#                 # Define the expected subfolder path
#                 expected_subfolder = (
#                     config["results_dir"] / "results_2024-10-09_15-33-23"
#                 )
#
#                 # Verify that console.print was called with the correct failure message
#                 expected_message = f"[bold red]Failed to create results subdirectory:[/bold red] {expected_subfolder}"
#                 mock_console.print.assert_any_call(expected_message)
#
#                 # Verify that logging.error was called with the correct message
#                 mock_logging.error.assert_called_with(
#                     f"Failed to create results subdirectory '{expected_subfolder}': Permission denied"
#                 )
#
#                 # Verify that sys.exit was called with 1
#                 mock_exit.assert_called_once_with(1)
