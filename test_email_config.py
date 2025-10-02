#!/usr/bin/env python3
"""
Test script to verify email configuration
Run this to test your email settings before using the forgot password feature
"""

import os
from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail, Message

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize mail
mail = Mail(app)

def test_email_configuration():
    """Test email configuration"""
    print("Testing Email Configuration...")
    print(f"MAIL_SERVER: {app.config['MAIL_SERVER']}")
    print(f"MAIL_PORT: {app.config['MAIL_PORT']}")
    print(f"MAIL_USE_TLS: {app.config['MAIL_USE_TLS']}")
    print(f"MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
    print(f"MAIL_PASSWORD: {'*' * len(app.config['MAIL_PASSWORD']) if app.config['MAIL_PASSWORD'] else 'NOT SET'}")
    print(f"MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")
    print("-" * 50)
    
    try:
        with app.app_context():
            # Create a test message
            msg = Message(
                subject='Email Configuration Test - Only',
                recipients=[app.config['MAIL_USERNAME']],  # Send to yourself
                sender=app.config['MAIL_DEFAULT_SENDER']
            )
            
            msg.body = """
            This is a test email to verify your email configuration.
            
            If you receive this email, your configuration is working correctly!
            
            Best regards,
            Only Team
            """
            
            # Send the email
            mail.send(msg)
            print("✅ SUCCESS: Email sent successfully!")
            print("Check your inbox for the test email.")
            
    except Exception as e:
        print("❌ ERROR: Failed to send email")
        print(f"Error details: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you're using an App Password (not your regular Gmail password)")
        print("2. Enable 2-Factor Authentication on your Google Account")
        print("3. Generate an App Password for 'Mail' application")
        print("4. Check that MAIL_USERNAME and MAIL_PASSWORD are correct in your .env file")

if __name__ == "__main__":
    test_email_configuration()
