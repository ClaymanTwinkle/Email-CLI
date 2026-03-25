from email.message import EmailMessage
from unittest.mock import MagicMock, patch

import pytest

from emailcli.sender import SmtpSender


@pytest.fixture
def sample_message():
    msg = EmailMessage()
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg["Subject"] = "Test"
    msg.set_content("Hello")
    return msg


@patch("emailcli.sender.smtplib.SMTP")
def test_smtp_starttls(mock_smtp_cls, sample_message):
    mock_smtp = MagicMock()
    mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

    sender = SmtpSender(
        host="smtp.example.com",
        port=587,
        username="user",
        password="pass",
        encryption="starttls",
    )
    sender.send(sample_message)

    mock_smtp_cls.assert_called_once_with("smtp.example.com", 587)
    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("user", "pass")
    mock_smtp.send_message.assert_called_once_with(sample_message)


@patch("emailcli.sender.smtplib.SMTP_SSL")
def test_smtp_ssl(mock_smtp_ssl_cls, sample_message):
    mock_smtp = MagicMock()
    mock_smtp_ssl_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp_ssl_cls.return_value.__exit__ = MagicMock(return_value=False)

    sender = SmtpSender(
        host="smtp.163.com",
        port=465,
        username="user",
        password="pass",
        encryption="ssl",
    )
    sender.send(sample_message)

    mock_smtp_ssl_cls.assert_called_once_with("smtp.163.com", 465)
    mock_smtp.login.assert_called_once_with("user", "pass")
    mock_smtp.send_message.assert_called_once_with(sample_message)


@patch("emailcli.sender.smtplib.SMTP")
def test_smtp_none_encryption(mock_smtp_cls, sample_message):
    mock_smtp = MagicMock()
    mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

    sender = SmtpSender(
        host="localhost",
        port=25,
        username="user",
        password="pass",
        encryption="none",
    )
    sender.send(sample_message)

    mock_smtp_cls.assert_called_once_with("localhost", 25)
    mock_smtp.starttls.assert_not_called()
    mock_smtp.login.assert_called_once_with("user", "pass")


@patch("emailcli.sender.smtplib.SMTP")
def test_smtp_send_failure(mock_smtp_cls, sample_message):
    from emailcli.exceptions import SendError

    mock_smtp = MagicMock()
    mock_smtp.send_message.side_effect = Exception("Connection refused")
    mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

    sender = SmtpSender(
        host="smtp.example.com",
        port=587,
        username="user",
        password="pass",
        encryption="starttls",
    )

    with pytest.raises(SendError, match="Connection refused"):
        sender.send(sample_message)
