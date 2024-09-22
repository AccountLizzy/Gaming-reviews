import mailtrap as mt


def send_text(receiver, message):
    mail = mt.Mail(
        sender=mt.Address(email="mailtrap@demomailtrap.com", name="Mailtrap Test"),
        to=[mt.Address(email=f"{receiver}")],
        subject="Customer Contact on Blog",
        text=f"{message}",
        category="Customer Interaction",
    )

    client = mt.MailtrapClient(token="f83369dffe84dd74df7a807856f6a8f1")
    client.send(mail)