import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_SENDER = os.getenv("SMTP_SENDER", "shulintech27@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_APP_PASSWORD") or os.getenv("EMAIL_APP_PASSWORD", "")


def send_otp_email(recipient_email: str, otp_code: str) -> dict:
    """
    Sends a 6-digit OTP password reset code to the recipient from shulintech27@gmail.com.
    If SMTP credentials are not yet configured or connect fails, logs to console
    and provides a dev fallback so testing is never blocked.
    """
    print(f"\n=======================================================")
    print(f" [GYANSETU OTP DISPATCH]")
    print(f" To: {recipient_email}")
    print(f" OTP Code: {otp_code}")
    print(f" Sender: {SMTP_SENDER}")
    print(f"=======================================================\n")

    if not SMTP_PASSWORD:
        print("[EMAIL SERVICE] SMTP_APP_PASSWORD not set. OTP logged above for development.")
        return {
            "success": True,
            "mode": "dev_console",
            "message": "OTP generated and logged to server console (SMTP password not configured).",
            "otp_preview": otp_code,
        }

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"GyanSetu - Password Reset Verification Code: {otp_code}"
        msg["From"] = f"GyanSetu Official <{SMTP_SENDER}>"
        msg["To"] = recipient_email

        text_content = f"""
Hello,

You requested a password reset for your GyanSetu account ({recipient_email}).
Your 6-digit verification code is:

{otp_code}

This code will expire in 10 minutes. If you did not make this request, please ignore this email.

Best regards,
GyanSetu Support Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; }}
    .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }}
    .logo {{ font-size: 20px; font-weight: 800; color: #1e3a8a; letter-spacing: 0.5px; margin-bottom: 20px; }}
    .code-box {{ background: #eff6ff; border: 1.5px dashed #3b82f6; border-radius: 8px; text-align: center; padding: 20px; margin: 24px 0; }}
    .code {{ font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #1d4ed8; font-family: monospace; }}
    .footer {{ font-size: 12px; color: #64748b; margin-top: 24px; border-top: 1px solid #e2e8f0; padding-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="logo">GYANSETU <span style="font-size: 12px; font-weight: 600; color: #0284c7; background: #e0f2fe; padding: 2px 8px; rounded: 4px;">OFFICIAL</span></div>
    <h2 style="font-size: 18px; color: #0f172a; margin-top: 0;">Password Reset Verification</h2>
    <p style="color: #475569; font-size: 14px; line-height: 1.6;">
      We received a request to reset the password for your GyanSetu account (<strong>{recipient_email}</strong>).
      Use the 6-digit verification code below to complete your password reset:
    </p>
    <div class="code-box">
      <div class="code">{otp_code}</div>
      <div style="font-size: 12px; color: #64748b; margin-top: 8px;">Valid for 10 minutes</div>
    </div>
    <p style="color: #64748b; font-size: 13px;">
      If you did not request this code, you can safely ignore this email. Your password will remain unchanged.
    </p>
    <div class="footer">
      National Official Statistics & Workforce Diagnostics Platform • GyanSetu
    </div>
  </div>
</body>
</html>
"""
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_SENDER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL SERVICE] Successfully sent OTP email to {recipient_email}")
        return {"success": True, "mode": "smtp", "message": f"Verification code sent to {recipient_email}"}
    except Exception as exc:
        print(f"[EMAIL SERVICE WARNING] SMTP send failed: {exc}. Falling back to dev mode.")
        return {
            "success": True,
            "mode": "dev_fallback",
            "message": f"Email delivery failed ({str(exc)}). OTP logged to console for testing.",
            "otp_preview": otp_code,
        }
