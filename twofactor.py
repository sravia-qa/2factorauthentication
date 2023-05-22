import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

def sendotp(email, otp):
    
        # Create a text/plain message
    msg = MIMEText("The otp is "+otp, 'plain', 'utf-8')

    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = 'The contents of files'
    msg['From'] = 'sravia@outlook.com'
    msg['To'] = email

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost:1025')
    s.sendmail('sravia@outlook.com', email, msg.as_string())
    s.quit()
    return True

