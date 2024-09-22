import mailtrap as mt
import os
from dotenv import load_dotenv

load_dotenv()

def send_text(receiver, message):
    mail = mt.Mail(
        sender=mt.Address(email="mailtrap@demomailtrap.com", name="Mailtrap Test"),
        to=[mt.Address(email=f"{receiver}")],
        subject="Customer Contact on Blog",
        text=f"{message}",
        category="Customer Interaction",
    )

    client = mt.MailtrapClient(token=f"{os.getenv('EMAIL_TOKEN')}")
    client.send(mail)