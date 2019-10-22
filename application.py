import os

from flask import Flask, session, render_template, request, redirect, url_for, jsonify, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import datetime
from functools import wraps
import requests
import json
from werkzeug.security import check_password_hash, generate_password_hash

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


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not "username" in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


db.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY,username TEXT, hash TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS reviews (id SERIAL PRIMARY KEY, review TEXT, rating INTEGER,\
book_id INTEGER REFERENCES books, user_id INTEGER REFERENCES users, date_time TIMESTAMP DEFAULT LOCALTIMESTAMP(0))")
db.commit()


@app.route("/", methods=["GET", "POST"])
@login_required
def search():
    if request.args.get("search"):
        
        matches = db.execute("SELECT isbn, title, author, year FROM (SELECT isbn, title, name author, date_id \
            FROM books LEFT JOIN authors ON authors.id = books.author_id) t1 LEFT JOIN dates t2 ON t2.id = t1.date_id\
                 WHERE isbn LIKE :search OR title LIKE :search OR author LIKE :search", {
                             "search": "%" + request.args.get("search") + "%"}).fetchall()
     
        if len(matches)==0:
            matches=None 

        return render_template("search.html", matches=matches, message="There are no matches for: \"" + request.args.get("search") + "\".")

    else:
        return render_template("search.html")


@app.route("/book/<string:isbn>", methods=["GET", "POST"])
@login_required
def book_page(isbn):
    
    book_row = db.execute("SELECT isbn, title, author, year, books_id FROM (SELECT isbn, title, name author, date_id,\
        books.id books_id FROM books LEFT JOIN authors ON authors.id = books.author_id) t1 LEFT JOIN dates t2 ON t2.id = t1.date_id WHERE isbn=:isbn", {
        "isbn": isbn}).fetchone()

    book_id = db.execute("SELECT * FROM books WHERE isbn=:isbn", {
            "isbn": isbn}).fetchone().id

    reviews = db.execute("SELECT username, review,  rating, date_time FROM reviews LEFT JOIN users ON users.id = reviews.user_id\
         WHERE book_id=:book_id ORDER BY date_time DESC", {
        "book_id": book_row.books_id}).fetchall()

    r = requests.get("https://www.goodreads.com/book/review_counts.json",
                     params={"key": "2MtQBfu3OpezX820klLyJw", "isbns": isbn})

    average_rating = json.loads(r.text)["books"][0]["average_rating"]
    ratings_count = json.loads(r.text)["books"][0]["ratings_count"]
    
    user_id = db.execute("SELECT * FROM users WHERE username=:username", {
        "username": session["username"]}).fetchone().id

    if len(reviews)==0:
        reviews=None

    if request.args.get("rating") and db.execute("SELECT * FROM reviews WHERE user_id=:user_id AND book_id=:book_id", {"user_id": user_id, "book_id": book_id}).rowcount != 0:
        flash("It is not allowed to post more than once for the same book.")
        return render_template("book.html", book_row=book_row, reviews=reviews, average_rating=average_rating, ratings_count=ratings_count)
    
    if request.args.get("review") and request.args.get("rating")==str(0):
        flash("Provide a rating")
        return render_template("book.html", book_row=book_row, reviews=reviews, average_rating=average_rating, ratings_count=ratings_count)

    elif not request.args.get("review") and request.args.get("rating") and request.args.get("rating") != str(0):

        flash("Provide a review")
        return render_template("book.html", book_row=book_row, reviews=reviews, average_rating=average_rating, ratings_count=ratings_count)

    elif not request.args.get("review") and request.args.get("rating") == str(0):

        flash("Provide a review and a rating")
        return render_template("book.html", book_row=book_row, reviews=reviews, average_rating=average_rating, ratings_count=ratings_count)

    elif request.args.get("review") and request.args.get("rating") != str(0):

        db.execute("INSERT INTO reviews (review, rating, book_id, user_id) VALUES (:review, :rating, :book_id, :user_id)", {
            "review": request.args.get("review"), "rating": request.args.get("rating"), "book_id": book_id, "user_id": user_id})

        reviews = db.execute("SELECT username, review,  rating, date_time FROM reviews LEFT JOIN users ON users.id = reviews.user_id WHERE \
            book_id=:book_id ORDER BY date_time DESC", {
            "book_id": book_row.books_id}).fetchall()

        db.commit()
        return redirect(url_for("book_page", isbn=isbn))

    return render_template("book.html", book_row=book_row, reviews=reviews, average_rating=average_rating, ratings_count=ratings_count)


@app.route("/api/<string:isbn>")
@login_required
def get_isbn(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn})
    if book.rowcount==1:
        book_row = book.fetchone()
        title = book_row.title
        author = db.execute("SELECT * FROM authors WHERE id=:id",{"id": book_row.author_id}).fetchone().name 
        year = db.execute("SELECT * FROM dates WHERE id=:id",{"id": book_row.date_id}).fetchone().year
        
        r = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "2MtQBfu3OpezX820klLyJw", "isbns": isbn})

        review_count = json.loads(r.text)["books"][0]["reviews_count"]
        average_score = json.loads(r.text)["books"][0]["average_rating"]

        return json.loads('{"title":"' + title + '", "author":"' + author + '", "year":"' + str(year) + '", "review_count":"'\
             + str(review_count) + '", "average_score":"' + average_score + '"}')    
    else:
        return render_template("error.html"),404


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        
        if not request.form.get("username") or not request.form.get("password"):
            return render_template("login.html", error="Must provide username and password.")
         
        user_row = db.execute("SELECT * FROM users WHERE username=:username", {"username": request.form.get("username")})
            
        if user_row.rowcount != 1 or not check_password_hash(user_row.fetchone().hash, request.form.get("password")):
            return render_template("login.html", error="Username or password incorrect.")

        else:
            session["username"] = db.execute("SELECT * FROM users WHERE username=:username", {
                                             "username": request.form.get("username")}).fetchone().username
            return redirect("/")
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirm_password"):
            return render_template("register.html", error="Must provide all the fields.")

        elif request.form.get("password") != request.form.get("confirm_password"):
            return render_template("register.html", error="The passwords don't match.")

        elif db.execute("SELECT * FROM users WHERE username=:username", {"username": request.form.get("username")}).rowcount != 0:
            return render_template("register.html", error="The username already exists.")

        else:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", \
                       {"username": request.form.get("username"), "hash": generate_password_hash(request.form.get("password"))})
            db.commit()
            session["username"] = db.execute(
                "SELECT * FROM users WHERE username=:username", {"username": request.form.get("username")}).fetchone().username
            return redirect("/")
    else:
        return render_template("register.html")


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    session.pop("username", None)
    return render_template("logout.html")

