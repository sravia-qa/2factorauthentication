from flask import Flask
from flask import request
import bcrypt
from cryptography.fernet import Fernet
import smtplib
import twofactor
#from sendgrid import SendGridAPIClient
#from sendgrid.helpers.mail import Mail
import random
from random import randint
from flask_mail import Message as MailMessage
import mysql.connector
from flask import current_app

#ONLY FOR DEV/TEST, DO NOT USE IN PRODUCTION


app = Flask(__name__)



def sendotp(id):
    otp = str(randint(100000, 999999))
    
    #generate hash for otp
    byt = otp.encode('utf-8')
    mysalt = bcrypt.gensalt()
    otphash = bcrypt.hashpw(byt, mysalt).decode("utf-8")
    mysalt = mysalt.decode("utf-8")
    print(otphash)
    print(mysalt)
    #add hash to database
    mycursor = mydb.cursor()
    sql = "UPDATE secureusers SET otp='"+otphash+"', otp_salt='"+mysalt+"' WHERE uname='" + id + "'" 
    mycursor.execute(sql)
    mydb.commit()
    if mycursor.rowcount == 1:
       

        try:
            twofactor.sendotp(id, otp)
            
            
            return True
        except Exception as e:
            return e.message
        
    else:
        return "there was a problem finding user, check the spelling again"


mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="yankeeD00dle!",
        database="sitedb"
        )
@app.route("/", methods = ['GET', 'POST'])
def home():
    if request.method == 'GET':
        f = open("home.html", 'r')
        c = f.read()
        f.close()
        return c
    if request.method == 'POST':
        uname = request.form['uname']
        upass = request.form['upass']
        #Get salt for this username
        mycursor = mydb.cursor()
        sql = "SELECT usalt, upass from secureusers WHERE uname = '"+uname+"'"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            return "incorrect username or password"
        mysalt = myresult[0][0]
        
        #hash password
        
        myencodedhash = bcrypt.hashpw(upass.encode('utf-8'), mysalt.encode("utf-8"))
        myhash = myencodedhash.decode("utf-8")

        # check if password is correct
        if(myhash == myresult[0][1]):
            #password correct, send OTP
            otpresult = sendotp(uname)
            if(otpresult == True):
                otppage = open("otp.html","r").read()
                
                return otppage

@app.route("/verifyotp", methods = ['GET', 'POST'])
def verifyotp():
    print('verifying otp now')
    if request.method == 'POST':
        uemail = request.form['email']
        uotp = request.form['otp']
        mycursor = mydb.cursor()
        sql = "SELECT otp,otp_salt from secureusers WHERE uname = '"+uemail+"'"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            return "incorrect username or password"
        saved_otp = myresult[0][0]
        saved_otp_salt = myresult[0][1]

        #Match saved_otp with the OTP received from user
        uotphash = bcrypt.hashpw(uotp.encode('utf-8'), saved_otp_salt.encode("utf-8"))
        myhash = uotphash.decode("utf-8")
        if(myhash == saved_otp):
            sql = "select usecret, ukey from secureusers WHERE uname ='"+uemail + "'" 
            mycursor.execute(sql)
            myresult = mycursor.fetchall()
            if len(myresult) == 0:
                return "incorrect username or otp"
            scrt = myresult[0][0]
            mykey = myresult[0][1]
            # decrypt secret
            decryptor = Fernet(mykey)
            dec_usecret = decryptor.decrypt(scrt)
            dec_usecret = dec_usecret.decode('utf-8')
            return dec_usecret
        else:
            return "Incorrect OTP, please begin from scratch. Try not to impersonate people."

        

@app.route("/newuser", methods = ['GET', 'POST'])
def createUser():
    if request.method == 'GET':
        f = open("create.html", 'r')
        c = f.read()
        f.close()
        return c
    if request.method == 'POST':
        uname = request.form['uname']
        upass = request.form['upass']
        usecret = request.form['usecret']
        #encrypt secret
        mykey = Fernet.generate_key()
        encryptor = Fernet(mykey)
        enc_usecret = encryptor.encrypt(usecret.encode())
        
        # hash pass
        byt = upass.encode('utf-8')
        mysalt = bcrypt.gensalt()
        myhash = bcrypt.hashpw(byt, mysalt)

        
        mycursor = mydb.cursor()
        sql = "INSERT into secureusers (uname, upass, usecret, ukey, usalt ) VALUES (%s, %s, %s, %s, %s)"
        #replace with correct encrypted and hashed values
        val = (uname, myhash, enc_usecret, mykey, mysalt)
        mycursor.execute(sql, val)
        mydb.commit()
        if mycursor.rowcount == 1:
            return "User Successfully Created"
        else:
            return "there was a problem creating user, try again after sometime"





mysslcontext = ('sravia.tech.crt', 'sravia.tech_key.txt')

       
app.run("0.0.0.0",port=8100, ssl_context=mysslcontext)
