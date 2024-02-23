import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from dotenv import load_dotenv
import os

load_dotenv()

def send_email(receiver_email, subject, body, image_path=None):
    sender_email = "hugozhan0802@gmail.com"
    password = os.getenv("GOOGLE_APP_PASS")

    # Setting up the MIME
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Attach the email body
    message.attach(MIMEText(body, "plain"))

    # Attach the image if path is provided
    if image_path:
        with open(image_path, 'rb') as image_file:
            image = MIMEImage(image_file.read(), name=os.path.basename(image_path))
            message.attach(image)

    # Send the email
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, password)
    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()
