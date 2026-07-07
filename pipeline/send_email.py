"""Email the daily Excel via Gmail SMTP.

Requires three GitHub secrets (or env vars):
  GMAIL_USER          your gmail address
  GMAIL_APP_PASSWORD  16-char app password (Google Account > Security > App passwords)
  EMAIL_TO            recipient (can be the same address)
Skips silently if secrets are absent, so the pipeline never fails on this.
"""
import os
import smtplib
from datetime import date
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run():
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    to = os.environ.get("EMAIL_TO", user)
    if not (user and pwd):
        print("Email secrets not set — skipping email step.")
        return

    xlsx = ROOT / "output" / "latest.xlsx"
    if not xlsx.exists():
        print("No Excel found — skipping email.")
        return

    msg = EmailMessage()
    msg["Subject"] = f"GehnaRadar trends — {date.today().isoformat()}"
    msg["From"], msg["To"] = user, to
    msg.set_content(
        "Aaj ki trending jewellery report attached hai.\n\n"
        "Sheets: Summary, All Items, Rising Searches, Category Interest, Source Status.\n"
        "Website bhi update ho chuki hai.\n\n— GehnaRadar (automated)"
    )
    msg.add_attachment(xlsx.read_bytes(), maintype="application",
                       subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       filename=f"GehnaRadar_{date.today().isoformat()}.xlsx")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pwd)
        s.send_message(msg)
    print(f"Emailed report to {to}")


if __name__ == "__main__":
    run()
