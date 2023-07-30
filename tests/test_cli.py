#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `pysonoff` package."""
import unittest
from click.testing import CliRunner
from pysonoff import cli
from tests.sonoff_mock import start_device, stop_device


class TestCLI(unittest.TestCase):
    """Tests for pysonoff CLI interface."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_cli_no_args(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.cli)
        assert (
            "No host name or device_id given, see usage below" in result.output
        )
        assert "Commands:" in result.output

    def test_cli_invalid_arg(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["hello"])
        print(result.output)
        assert 'Error: No such command' in result.output

    def test_cli_help(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["--help"])
        assert result.exit_code == 0
        assert "Show this message and exit." in result.output

    def test_cli_version(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["--version"])
        assert result.exit_code == 0
        assert ", version" in result.output

    def test_cli_no_device_id(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["--device_id"])
        assert (
            "Error: --device_id option requires an argument" in result.output
        )

    def test_cli_no_host_id(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["--host"])
        assert "Error: --host option requires an argument" in result.output

    def test_cli_state_error(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["state"])
        assert (
            "No host name or device_id given, see usage below" in result.output
        )

    def test_cli_state(self):

        start_device("StateMock", "plug")

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["--device_id", "StateMock", "state"])

        print(result.output)

        assert "info: State: OFF" in result.output

        stop_device()

    def test_cli_on(self):

        start_device("PlugOnMock", "plug")

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["--device_id", "PlugOnMock", "on"])

        print(result.output)

        assert "info: State: ON" in result.output

        stop_device()

    def test_cli_off(self):

        start_device("PlugOffMock", "plug")

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["--device_id", "PlugOffMock", "off"])

        print(result.output)

        assert "info: State: OFF" in result.output

        stop_device()

    def test_cli_on_strip(self):

        start_device("StripOnMock", "strip")

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["--device_id", "StripOnMock", "on"])

        print(result.output)

        assert "info: State: ON" in result.output

        stop_device()

    def test_cli_off_strip(self):

        start_device("StripOffMock", "strip")

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["--device_id", "StripOffMock", "on"])

        print(result.output)

        assert "info: State: OFF" in result.output

        stop_device()

    def test_cli_on_encrypt(self):

        start_device("PlugEncryptMock", "plug", "testkey")

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--device_id", "PlugEncryptMock", "--api_key", "testkey", "on"],
        )

        print(result.output)

        assert "info: State: ON" in result.output

    def test_cli_on_strip_encrypt(self):

        start_device("StripEncryptMock", "strip", "testkey")

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            [
                "--device_id",
                "StripEncryptMock",
                "--api_key",
                "testkey",
                "-l",
                "DEBUG",
                "on",
            ],
        )

        print(result.output)

        assert "info: State: ON" in result.output

        stop_device()

    def test_cli_discover(self):

        start_device("DiscoverMock", "plug")

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["discover"])

        print(result.output)

        assert (
            "Attempting to discover Sonoff LAN Mode devices on the local "
            "network" in result.output
        )
        assert "DiscoverMock" in result.output

        stop_device()

    def test_cli_discover_debug(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["-l", "DEBUG", "discover"])
        assert (
            "Looking for all eWeLink devices on local network" in result.output
        )

    def test_cli_no_key(self):

        start_device("PlugEncryptMock2", "plug", "testkey")

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(
            cli.cli, ["--device_id", "PlugEncryptMock2", "state"],
        )

        print(result.output)

        assert "Missing api_key for encrypted device" in result.output

    def test_cli_wrong_key(self):

        start_device("PlugEncryptMock3", "plug", "testkey")

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--device_id", "PlugEncryptMock3", "--api_key", "bad", "state"],
        )

        print(result.output)

        assert "Probably wrong API key" in result.output

    def test_cli_reconnect(self):

        start_device("ReconnectMock", "plug", None, None, None, "Reconnect")

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            [
                "--device_id",
                "ReconnectMock",
                "-l",
                "DEBUG",
                "--wait",
                "2",
                "listen",
            ],
        )

        print(result.output)

        assert "still active!" in result.output
        assert "added again" in result.output

        stop_device()

    def test_cli_reconnect_strip(self):

        start_device(
            "ReconnectStripMock", "strip", None, None, None, "Reconnect"
        )

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            [
                "--device_id",
                "ReconnectStripMock",
                "-l",
                "DEBUG",
                "--wait",
                "2",
                "listen",
            ],
        )

        print(result.output)

        assert "still active!" in result.output
        assert "added again" in result.output

        stop_device()

    def test_cli_disconnect(self):

        start_device("DisconnectMock", "plug", None, None, None, "Disconnect")

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            [
                "--device_id",
                "DisconnectMock",
                "-l",
                "DEBUG",
                "--wait",
                "3",
                "listen",
            ],
        )

        print(result.output)

        assert "removed" in result.output
        assert "added" in result.output
        assert "sending 'available'" in result.output.partition("removed")[2]

        stop_device()

    def test_cli_disconnect_encrypt(self):

        start_device(
            "DisconnectEncryptMock",
            "strip",
            "testkey",
            None,
            None,
            "Disconnect",
        )

        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            [
                "--device_id",
                "DisconnectEncryptMock",
                "--api_key",
                "testkey",
                "-l",
                "INFO",
                "--wait",
                "3",
                "listen",
            ],
        )

        print(result.output)

        assert "removed" in result.output
        assert "added" in result.output
        assert "sending 'available'" in result.output.partition("removed")[2]

        stop_device()

    """
    def test_cli_on_off(self):

        start_device("InchingMock", "plug")

        # Test the CLI.
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["--device_id",
             "InchingMock", "--inching", "2", "on"])

        print(result.output)

        assert "info: State: ON" in result.output
        assert "info: State: OFF" in result.output.partition("State: ON")[2]

        stop_device()
    """


if __name__ == "__main__":
    unittest.main()
