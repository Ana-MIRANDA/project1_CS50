#here we are going to import the document books.csv
         
import csv #fazer a relaçao com o csv instalado c o pip 
import os 

import time

#Aqui pede-se o sqlalchemy para se poder aceder à base de dados
from sqlalchemy import create_engine                             
from sqlalchemy.orm import scoped_session, sessionmaker   

#Database
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine,autocommit=False))
# print(os.getenv("DATABASE_URL")) - to test if the DB was well set

content = open("books.csv") # na variavel content/conteudo em pt guarda-se a feature open/abrir o documento csv
allBooks = csv.reader(content) #em allbooks guarda-se o conteud do documento
for isbn, title, author, year in allBooks:
   # try: #fizemos este try pk no doc books.csv o primeiro n é um int é uma str pk tem escrito year. Assim criamos a variavel y como a q guarda int e no except so saem so que nao forem int que é so a palavra year 
    try:
        y = int(year)
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:i, :t, :a, :y)", {"i": isbn, "t": title, "a": author, "y": int(y)}) 
        print(f"Inserted {title}") 
    except:
        print(f"This one did not work {title}")
        time.sleep(2) #colocamos isto aqui pk como eram muitos livros e a DB e externa para lhe dar tempo de 2 segundos para guardar cada livro
db.commit()