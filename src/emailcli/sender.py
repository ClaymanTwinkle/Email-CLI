import smtplib
from abc import ABC, abstractmethod
from email.message import EmailMessage

from emailcli.exceptions import SendError


class Sender(ABC):
    @abstractmethod
    def send(self, message: EmailMessage) -> None: ...


class SmtpSender(Sender):
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        encryption: str,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.encryption = encryption

    def send(self, message: EmailMessage) -> None:
        try:
            if self.encryption == "ssl":
                smtp_cls = smtplib.SMTP_SSL
            else:
                smtp_cls = smtplib.SMTP

            with smtp_cls(self.host, self.port) as server:
                if self.encryption == "starttls":
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(message)
        except SendError:
            raise
        except Exception as e:
            raise SendError(f"Failed to send email: {e}") from e
