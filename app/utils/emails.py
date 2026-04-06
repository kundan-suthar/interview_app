from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

async def send_verification_email(email: str, link: str):
    message = MessageSchema(
        subject="Verify your email",
        recipients=[email],
        body=f"Click here to verify: {link}",
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    print("mail sent")
    print("-------------------------------------")