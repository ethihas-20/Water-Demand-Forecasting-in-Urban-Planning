import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email Configuration
SENDER_EMAIL = "ethihasanand2003@gmail.com"
RECEIVER_EMAIL = "gganes404@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
PORT = 587
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_alert_email(city, zone, date, predicted_demand, alert_message):
    """
    Send email alert based on zone-level thresholds.

    Args:
        city (str): City name
        zone (str): Zone name
        date (str): Date in YYYY-MM-DD format
        predicted_demand (float): Predicted water demand in MLD
        alert_message (str): Alert message if any

    Returns:
        str: "sent" if email sent, "no alert" if no alert triggered, "failed" if error
    """
    if alert_message is None:
        return "no alert"

    if "LOW" in alert_message:
        subject = f"⚠️ Low Water Demand Alert – {city} - {zone}"
    elif "HIGH" in alert_message:
        subject = f"🚨 High Water Demand Alert – {city} - {zone}"
    else:
        subject = f"⚠️ Water Demand Alert – {city} - {zone}"

    body = f"""City: {city}
Zone: {zone}
Date: {date}
Predicted Demand: {predicted_demand:.2f} MLD
Threshold breached: {alert_message}
Alert message: {alert_message}"""

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send email
        server = smtplib.SMTP(SMTP_SERVER, PORT)
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, text)
        server.quit()

        return "sent"
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return "failed"