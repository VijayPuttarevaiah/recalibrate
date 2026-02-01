# Import smtplib for sending emails via SMTP protocol
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config.config import Config

# Initialize configuration
config = Config()

# Function to send an email using the SMTP settings from the configuration
def send_email(to_email: str, subject: str, body: str) -> None:
    # Retrieve SMTP configuration settings
    smtp_server = config.config['email']['smtp_server']
    smtp_port = int(config.config['email']['smtp_port'] or 587)
    smtp_user = config.config['email']['smtp_user']
    smtp_password = config.config['email']['smtp_password']

    # Ensure SMTP credentials are provided
    if not smtp_user or not smtp_password:
        raise ValueError('SMTP_USER and SMTP_PASSWORD must be set as environment variables')

    # Construct the email message
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    # Attach the email body content
    msg.attach(MIMEText(body, 'plain'))

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        # Secure the connection using TLS
        server.starttls()
        # Authenticate with the SMTP server
        server.login(smtp_user, smtp_password)
        # Send the finalized email message
        server.send_message(msg)
