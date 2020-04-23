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

                                                                   #Route 2- search books                                                        
@app.route("/search", methods=['GET'])
def searchBooks():
    return render_template("search_books.html")

@app.route("/search", methods=['POST'])
def getBooks():
    getInfoSearch = request.form.get("pesquisa")
    getSearchFor = request.form.get("searchFor") 
    infowithwildcards=  {"gis": f"%{getInfoSearch}%"} # to not repeat all this in the 4 queries below

    if getInfoSearch == "":
        return render_template("search_books.html", messageError="Write something to start your research!") #if user clics go without writting something
    elif getSearchFor == "isbn":
        filteredBooks = db.execute(" SELECT * FROM books WHERE isbn ILIKE :gis", infowithwildcards).fetchall()
    elif getSearchFor == "title":
        filteredBooks = db.execute(" SELECT * FROM books WHERE title ILIKE :gis", infowithwildcards).fetchall()
    elif getSearchFor == "author":
        filteredBooks = db.execute(" SELECT * FROM books WHERE author ILIKE :gis", infowithwildcards).fetchall()
    else:
        filteredBooks = db.execute("select * from books where isbn ilike :gis or title ilike :gis or author ilike :gis", infowithwildcards).fetchall()

    return render_template("search_books.html", getb=filteredBooks, )

                                                                   #Route 3 - register account 

@app.route("/registerAccount", methods=['POST'])
def newAccountInfo(): 
    getUserName = request.form.get("name")
    getUserEmail = request.form.get("email")
    getUserPassword = request.form.get("psw")
    getUserRepeatPassword = request.form.get("psw-repeat")
  
    #verify if the password matchs with reapeat password
    if (getUserRepeatPassword == getUserPassword):
         return redirect(url_for('searchBooks'))
    else:
        return render_template("presentation_page.html", messageError="You didn't repeat the right password!")

    sameEmail = db.execute("SELECT users.email FROM users WHERE users.email = :email",{"email": getUserEmail}).fetchone()
   
   #verify if the email already exists
    if sameEmail == None: 
        db.execute("INSERT INTO users (name, email, password) VALUES (:n, :e, :p)",{"n": getUserName, "e": getUserEmail, "p": getUserPassword})
        db.commit()
        user_id= db.execute("SELECT * FROM users WHERE email = :e ", {"e": getUserEmail}).fetchone() 
       
        sessions(user_id) 
        return redirect(url_for('searchBooks'))
    else: 
        return render_template("presentation_page.html", msgEmailExists="That email account already exists!")

   
    
                                                                   #Route 4 - log in and verify if passwrd matches
@app.route("/login", methods=['POST'])
def login_verify(): 
    #get info from form login

    userEmailLogin = request.form.get("userEmail")
    userPassLogin = request.form.get("userPassword")
    queryvalues = {"e": userEmailLogin, "p": userPassLogin}

    #verify if user exists in table users
    usersAre = db.execute("SELECT * FROM users WHERE email = :e AND password = :p", queryvalues).fetchall()

    #in case of error
    if not usersAre:
         return render_template("presentation_page.html", ups="Email and/or Password incorrect(s)!")
    else:
        sessions(usersAre[0]) # invocation of function sessions with id_user as parameter
        return redirect(url_for('searchBooks'))


                                                                   # Sessions 
    #After log the users id will be stored in sessions
    #sessions:  so the user could rate and write reviews and we could keep that info in the table and visible in the page web
def sessions(user):
    if session.get("id_user") is None:
        session["id_user"] = user
                                                             #Route 5 - log out and clean sessions 

@app.route("/logout", methods=['GET'])
def logout():
    session.pop('id_user', None)
    return redirect(url_for('initial_page'))

                                                                 #Route 6 - book page : 
@app.route("/bookpage/<int:idNoUrl>", methods=['GET']) 
def infoBooks(idNoUrl):
    infoSelectedBook= db.execute("SELECT * FROM books WHERE id = :bookid", {"bookid": idNoUrl}).fetchone()
#For Goodreads
    avgGoodR= getFromGoodreads(infoSelectedBook.isbn)['average_rating'] #este average_rating esta usada na api do goodreads
    rateCountGoodR= getFromGoodreads(infoSelectedBook.isbn)['work_ratings_count']
    

    reviewsAllInfo=db.execute("SELECT users.name, comments.review, comments.rate FROM comments LEFT JOIN users ON comments.user_id = users.id WHERE comments.book_id=:book_id ORDER BY comments.id DESC", {"book_id": idNoUrl}).fetchall()
    
    if "messageError" in request.args: 
        msgError= request.args['messageError'] 
        return render_template("book_page.html", seleSctedBook= idNoUrl, bookInfo= infoSelectedBook, ratesAndComments = reviewsAllInfo, messageError=msgError)

    return render_template("book_page.html", seleSctedBook= idNoUrl, bookInfo= infoSelectedBook, ratesAndComments = reviewsAllInfo, ratingMedia=avgGoodR, ratenumber=rateCountGoodR)
    
#For Goodreads                                                               
def getFromGoodreads(isbn):
    res = requests.get(f"https://www.goodreads.com/book/review_counts.json?isbns={isbn}&format=json&key=s8o3qMgESTFq7XwnKTIqw")
    resposta= res.json()
    return(resposta['books'][0])

                                                #Get in the form user's rate and comment for the selected book and submit them 
@app.route("/bookpage/<int:idbook>", methods=['POST'])
def userComments(idbook):
    getRate= request.form.get("rate")
    getComment= request.form.get("commentOfUser")

    aUserOnecomment = db.execute("SELECT user_id FROM comments WHERE user_id = :u AND comments.book_id=:book_id " , {"u":session['id_user'][0],"book_id": idbook}).fetchone()
    
    if aUserOnecomment == None: 
        rateAndComment = db.execute("INSERT INTO comments (book_id, user_id, review, rate) VALUES (:b, :u, :r, :ra)", {"b":idbook , "u":session['id_user'][0], "r":getComment, "ra":getRate})
        
        db.commit()
        return redirect(url_for('infoBooks', idNoUrl=idbook))
    else:
        return redirect(url_for('infoBooks', idNoUrl=idbook, messageError="You've already submitted your review for this book!")) 

                                                                    #Route 7 -/api/<isbn> route - search for isbn with GET  
                                                     #return an bject with:  title, author, publication date, ISBN number, review count, and average score.  
    
@app.route("/api/<isbn>", methods=['GET'])
def api(isbn):
    allFromIsbnBook = db.execute("SELECT * FROM books WHERE books.isbn = :i",{"i": isbn}).fetchone() 
   
    book_id= allFromIsbnBook[0] 
    ratesByIsbn = db.execute("SELECT COUNT(rate) FROM comments WHERE book_id = :i GROUP BY book_id",{"i": book_id}).fetchone() 
    
    averageByIsbn = db.execute("SELECT AVG(rate) FROM comments WHERE book_id = :i GROUP BY book_id",{"i": book_id}).fetchone()
  
    allIsbnSearch = {"title":allFromIsbnBook[2] , "author": allFromIsbnBook[3] ,"year": allFromIsbnBook[4] ,"isbn": allFromIsbnBook[1], "review_count":ratesByIsbn[0], "average_score":str(averageByIsbn[0])}   
    
    return allIsbnSearch

   