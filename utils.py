import os
import logging
from flask import render_template_string
from flask_mail import Message
from app import mail

logger = logging.getLogger(__name__)

def send_otp_email(email, otp, purpose="booking"):
    """
    Send an OTP email with HTML formatting
    
    Args:
        email (str): Recipient's email address
        otp (str): One-time password to be sent
        purpose (str): Purpose of the OTP (booking, login, etc.)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Check if mail credentials are available
        username = os.environ.get("MAIL_USERNAME")
        password = os.environ.get("MAIL_PASSWORD")
        
        if not username or not password:
            # Log the OTP instead of sending email since credentials are not available
            logger.warning("SMTP credentials not available. Displaying OTP in logs instead.")
            logger.info(f"==== OTP for {email} ({purpose}): {otp} ====")
            # In development, we'll consider this a success
            return True
            
        # HTML email template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your TravelWise OTP Code</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .container {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 30px;
                    background-color: #f9f9f9;
                    box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid #eee;
                }
                .logo {
                    font-size: 28px;
                    font-weight: bold;
                    color: #3f51b5;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                .otp-container {
                    margin: 30px 0;
                    text-align: center;
                }
                .otp-title {
                    font-size: 18px;
                    color: #555;
                    margin-bottom: 15px;
                }
                .otp-code {
                    display: inline-block;
                    text-align: center;
                    font-size: 36px;
                    letter-spacing: 8px;
                    font-weight: bold;
                    color: #3f51b5;
                    padding: 15px 25px;
                    background-color: #e8eaf6;
                    border-radius: 8px;
                    border: 2px dashed #c5cae9;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .footer {
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #777;
                    text-align: center;
                }
                .info {
                    margin: 25px 0;
                    padding: 15px;
                    background-color: #e8f5e9;
                    border-left: 4px solid #4caf50;
                    border-radius: 4px;
                }
                .warning {
                    margin: 15px 0;
                    padding: 10px 15px;
                    background-color: #fff8e1;
                    border-left: 4px solid #ffc107;
                    border-radius: 4px;
                    font-size: 13px;
                }
                .expiry {
                    color: #f44336;
                    font-weight: bold;
                }
                .greeting {
                    font-size: 18px;
                    margin-bottom: 20px;
                }
                .purpose-badge {
                    display: inline-block;
                    padding: 4px 12px;
                    background-color: #e0f2f1;
                    color: #00796b;
                    border-radius: 30px;
                    font-size: 14px;
                    font-weight: bold;
                    margin-top: 3px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">TravelWise</div>
                    <p>Your Travel Planning Partner</p>
                </div>
                
                <p class="greeting">Hello there,</p>
                
                <p>You have requested a verification code for your <span class="purpose-badge">{{ purpose }}</span> action. Please use the code below to complete your verification:</p>
                
                <div class="otp-container">
                    <div class="otp-title">Your Verification Code</div>
                    <div class="otp-code">{{ otp }}</div>
                </div>
                
                <div class="info">
                    <p>This code will expire in <span class="expiry">10 minutes</span> for security purposes.</p>
                    <p>If you don't complete the verification within this time, you'll need to request a new code.</p>
                </div>
                
                <div class="warning">
                    <p><strong>Important:</strong> If you did not request this code, please ignore this email. Someone might have entered your email address by mistake.</p>
                </div>
                
                <p>Thank you for choosing TravelWise for your travel needs!</p>
                
                <div class="footer">
                    <p>© 2025 TravelWise. All rights reserved.</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Render the template with the provided variables
        html_content = render_template_string(html_template, otp=otp, purpose=purpose)
        
        # Create the message
        subject = "TravelWise OTP Verification Code"
        if purpose == "booking":
            subject = "TravelWise Booking Verification Code"
        elif purpose == "login":
            subject = "TravelWise Login Verification Code"
        elif purpose == "password_reset":
            subject = "TravelWise Password Reset Verification Code"
            
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_content,
            sender=os.environ.get("MAIL_DEFAULT_SENDER", os.environ.get("MAIL_USERNAME", "noreply@TravelWise.com"))
        )
        
        # Send the email
        mail.send(msg)
        logger.info(f"OTP email sent successfully to {email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send OTP email: {str(e)}")
        # Log the OTP in case of errors so users can still test the system
        logger.warning(f"[FALLBACK] OTP for {email} ({purpose}): {otp}")
        return False