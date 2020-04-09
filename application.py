import os

import requests

from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


                                                                    #Route 1 - presentation_page

@app.route("/", methods=['GET'])
def initial_page():
    return render_template("presentation_page.html")



@app.route("/search", methods=['GET'])
def after_loggedIn():
    return render_template("after_login.html")

                                                                   #Route 3 to register account 

@app.route("/registerAccount", methods=['POST'])
def newAccountInfo(): #get all info from form create account 
    getUserName = request.form.get("name")
    getUserEmail = request.form.get("email")
    getUserPassword = request.form.get("psw")
    getUserRepeatPassword = request.form.get("psw-repeat")

    # store all info in a variable (always verify if the DATABASE_URL variable is well set )
    db.execute("INSERT INTO users (name, email, password) VALUES (:n, :e, :p)",{"n": getUserName, "e": getUserEmail, "p": getUserPassword})
    db.commit()

    #verify if the password = reapeat password
    if (getUserRepeatPassword == getUserPassword ):
         return redirect(url_for('after_loggedIn'))
    else:
        return render_template("presentation_page.html", messageError="You didnt repeat the right password!")
    

    

# to sent to the table users