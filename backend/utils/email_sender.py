import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.config import Config

config = Config()

def send_email(to_email: str, subject: str, body: str) -> None:
    # These should be set in environment variables or config for security
    smtp_server = config.config['email']['smtp_server']
    smtp_port = int(config.config['email']['smtp_port'] or 587)
    smtp_user = config.config['email']['smtp_user']
    smtp_password = config.config['email']['smtp_password']

    if not smtp_user or not smtp_password:
        raise ValueError('SMTP_USER and SMTP_PASSWORD must be set as environment variables')

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
