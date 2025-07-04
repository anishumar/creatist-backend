from __future__ import annotations

import os
from email.message import EmailMessage

from aiosmtplib import send

os.environ["SSL_CERT_FILE"] = "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/certifi/cacert.pem"

with open("static/otp-content.html", "r") as file:
    OTP_CONTENT = file.read()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_FROM = os.getenv("EMAIL_FROM", "Creatist <no-reply@creatist.site>")


async def send_otp_mail(email_address: str, otp: str) -> None:
    message = EmailMessage()
    message["From"] = EMAIL_FROM
    message["To"] = email_address
    message["Subject"] = "Your Creatist OTP - Secure Access"
    message.set_content(OTP_CONTENT.format(otp=otp), subtype="html")

    await send(
        message,
        hostname=EMAIL_HOST,
        port=EMAIL_PORT,
        start_tls=True,
        username=EMAIL_ADDRESS,
        password=EMAIL_PASSWORD,
    )
    print("EMAIL SENT")
