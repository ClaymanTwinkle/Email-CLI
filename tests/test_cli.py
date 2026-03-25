from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from click.testing import CliRunner

from emailcli.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def config_home(tmp_path):
    config_dir = tmp_path / ".emailcli"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text(yaml.dump({
        "from": "me@example.com",
        "smtp": {
            "host": "smtp.example.com",
            "port": 587,
            "username": "me@example.com",
            "password": "secret",
            "encryption": "starttls",
        },
    }))
    return config_dir


@patch("emailcli.cli.SmtpSender")
def test_send_plain_text(mock_sender_cls, runner, config_home):
    mock_sender = MagicMock()
    mock_sender_cls.return_value = mock_sender

    result = runner.invoke(cli, [
        "send",
        "--to", "recipient@example.com",
        "--subject", "Hello",
        "--body", "Hello World",
        "--config-dir", str(config_home),
    ])
    assert result.exit_code == 0
    mock_sender.send.assert_called_once()


@patch("emailcli.cli.SmtpSender")
def test_send_html(mock_sender_cls, runner, config_home):
    mock_sender = MagicMock()
    mock_sender_cls.return_value = mock_sender

    result = runner.invoke(cli, [
        "send",
        "--to", "recipient@example.com",
        "--subject", "Report",
        "--html", "<h1>Report</h1>",
        "--config-dir", str(config_home),
    ])
    assert result.exit_code == 0
    mock_sender.send.assert_called_once()


@patch("emailcli.cli.SmtpSender")
def test_send_with_attachment(mock_sender_cls, runner, config_home, tmp_path):
    mock_sender = MagicMock()
    mock_sender_cls.return_value = mock_sender

    attach_file = tmp_path / "report.pdf"
    attach_file.write_bytes(b"%PDF-1.4")

    result = runner.invoke(cli, [
        "send",
        "--to", "recipient@example.com",
        "--subject", "Report",
        "--body", "See attached",
        "--attach", str(attach_file),
        "--config-dir", str(config_home),
    ])
    assert result.exit_code == 0
    mock_sender.send.assert_called_once()


@patch("emailcli.cli.SmtpSender")
def test_send_multiple_recipients(mock_sender_cls, runner, config_home):
    mock_sender = MagicMock()
    mock_sender_cls.return_value = mock_sender

    result = runner.invoke(cli, [
        "send",
        "--to", "a@example.com",
        "--to", "b@example.com",
        "--subject", "Multi",
        "--body", "Hello",
        "--config-dir", str(config_home),
    ])
    assert result.exit_code == 0


def test_send_no_body_or_html(runner, config_home):
    result = runner.invoke(cli, [
        "send",
        "--to", "recipient@example.com",
        "--subject", "Empty",
        "--config-dir", str(config_home),
    ])
    assert result.exit_code != 0
    assert "body" in result.output.lower() or "html" in result.output.lower()


def test_send_no_config(runner, tmp_path):
    result = runner.invoke(cli, [
        "send",
        "--to", "recipient@example.com",
        "--subject", "Hello",
        "--body", "text",
        "--config-dir", str(tmp_path / "nonexistent"),
    ])
    assert result.exit_code != 0
    assert "init" in result.output.lower()


@patch("emailcli.cli.SmtpSender")
def test_send_from_override(mock_sender_cls, runner, config_home):
    mock_sender = MagicMock()
    mock_sender_cls.return_value = mock_sender

    result = runner.invoke(cli, [
        "send",
        "--to", "recipient@example.com",
        "--subject", "Override",
        "--body", "text",
        "--from", "other@example.com",
        "--config-dir", str(config_home),
    ])
    assert result.exit_code == 0
    # Verify the message was built with overridden from
    sent_msg = mock_sender.send.call_args[0][0]
    assert sent_msg["From"] == "other@example.com"


@patch("emailcli.cli.SmtpSender")
def test_send_stdin_body(mock_sender_cls, runner, config_home):
    mock_sender = MagicMock()
    mock_sender_cls.return_value = mock_sender

    result = runner.invoke(cli, [
        "send",
        "--to", "recipient@example.com",
        "--subject", "Stdin",
        "--body", "-",
        "--config-dir", str(config_home),
    ], input="Hello from stdin\n")
    assert result.exit_code == 0
    mock_sender.send.assert_called_once()


def test_send_html_and_html_file_exclusive(runner, config_home, tmp_path):
    html_file = tmp_path / "template.html"
    html_file.write_text("<h1>Test</h1>")

    result = runner.invoke(cli, [
        "send",
        "--to", "recipient@example.com",
        "--subject", "Conflict",
        "--html", "<p>inline</p>",
        "--html-file", str(html_file),
        "--config-dir", str(config_home),
    ])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower() or "exclusive" in result.output.lower()
