from email.message import EmailMessage

import logging, os, smtplib, ssl

logger = logging.getLogger(__name__)

def sendEmail(message, subject):
    msg = EmailMessage()

    msg.set_content(message)
    msg["Subject"] = subject
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["MAIL_TO"]

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(
        os.environ["SMTP_HOST"],
        int(os.getenv("SMTP_PORT", "465")),
        context=context,
        timeout=15
    ) as smtp:
        smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])

        smtp.send_message(msg)

        logger.info(
            "Email submitted successfully to %s (subject: %s)",
            msg["To"],
            msg["Subject"]
        )
