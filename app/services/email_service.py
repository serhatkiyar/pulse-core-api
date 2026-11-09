import logging
import smtplib
from email.message import EmailMessage

from ..config import settings

logger = logging.getLogger(__name__)


def send_welcome_email(to_email: str, name: str):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Pulse Core'a Hoş Geldiniz!"
        msg["From"] = "noreply@pulse.com"
        msg["To"] = to_email
        msg.set_content(f"Merhaba {name},\n\nHesabınız başarıyla oluşturuldu.")

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.send_message(msg)
    except Exception as e:
        logger.error(f"Hoş geldin e-postası gönderilemedi ({to_email}): {e}")
