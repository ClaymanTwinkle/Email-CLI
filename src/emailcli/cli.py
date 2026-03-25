import sys
from pathlib import Path

import click

from emailcli.config import load_config
from emailcli.exceptions import EmailCliError
from emailcli.message import build_message
from emailcli.sender import SmtpSender


@click.group()
def cli():
    """CLI tool for sending emails with attachments."""


@cli.command()
@click.option("--to", "to_addrs", required=True, multiple=True, help="Recipient email address (repeatable).")
@click.option("--subject", required=True, help="Email subject.")
@click.option("--body", default=None, help="Plain text body. Use '-' to read from stdin.")
@click.option("--html", "html_content", default=None, help="HTML body string.")
@click.option("--html-file", "html_file_path", default=None, type=click.Path(exists=True), help="Read HTML body from file.")
@click.option("--attach", "attachments", multiple=True, type=click.Path(exists=True), help="Attachment file path (repeatable).")
@click.option("--from", "from_addr", default=None, help="Sender address (overrides config).")
@click.option("--config-dir", default=None, type=click.Path(), hidden=True, help="Config directory (for testing).")
def send(to_addrs, subject, body, html_content, html_file_path, attachments, from_addr, config_dir):
    """Send an email."""
    try:
        # Validate --html and --html-file mutual exclusivity
        if html_content and html_file_path:
            raise click.UsageError("--html and --html-file are mutually exclusive.")

        # Read stdin if body is "-"
        if body == "-":
            body = click.get_text_stream("stdin").read()

        # Load config
        cfg_dir = Path(config_dir) if config_dir else None
        config = load_config(cfg_dir)

        # Determine from address
        sender_addr = from_addr or config.from_addr
        if not sender_addr:
            raise EmailCliError("No sender address. Set 'from' in config or use --from.")

        # Build message
        msg = build_message(
            from_addr=sender_addr,
            to_addrs=list(to_addrs),
            subject=subject,
            body=body,
            html=html_content,
            html_file=Path(html_file_path) if html_file_path else None,
            attachments=[Path(a) for a in attachments] if attachments else None,
        )

        # Send
        sender = SmtpSender(
            host=config.smtp_host,
            port=config.smtp_port,
            username=config.smtp_username,
            password=config.smtp_password,
            encryption=config.smtp_encryption,
        )
        sender.send(msg)

        click.echo("Email sent successfully.")
    except click.UsageError:
        raise
    except EmailCliError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
