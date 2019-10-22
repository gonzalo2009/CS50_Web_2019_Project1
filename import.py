import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")


engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

db.execute(
    "DROP TABLE IF EXISTS books CASCADE; DROP TABLE IF EXISTS authors CASCADE; DROP TABLE IF EXISTS dates CASCADE")

db.execute(
    "CREATE TABLE authors (id SERIAL PRIMARY KEY, name VARCHAR UNIQUE)")
db.execute(
    "CREATE TABLE dates (id SERIAL PRIMARY KEY, year INTEGER UNIQUE)")

f = open("books.csv")
reader = csv.reader(f)

next(reader)

db.execute("CREATE TABLE books (id SERIAL PRIMARY KEY, isbn VARCHAR, title VARCHAR, author VARCHAR, year INTEGER)")


for row in reader:
    db.execute("INSERT INTO books (isbn, title, author ,year) VALUES (:isbn, :title, :author, :year)", {
        "isbn": row[0], "title": row[1], "author": row[2], "year": row[3]})



authors_list = db.execute("SELECT * FROM books").fetchall()
   
for row in authors_list:
    db.execute("INSERT INTO authors (name) VALUES (:name) ON CONFLICT (name) DO NOTHING", {
        "name": row["author"]})

authors_list = db.execute("SELECT * FROM authors ORDER BY name").fetchall()

db.execute("DELETE FROM authors; ALTER SEQUENCE authors_id_seq RESTART WITH 1")

for row in authors_list:
    db.execute("INSERT INTO authors (name) VALUES (:name)", {
        "name": row["name"]})


dates_list = db.execute("SELECT * FROM books").fetchall()

for row in dates_list:
    db.execute("INSERT INTO dates (year) VALUES (:year) ON CONFLICT (year) DO NOTHING", {
        "year": row["year"]})

dates_list = db.execute("SELECT * FROM dates ORDER BY year").fetchall()

db.execute("DELETE FROM dates; ALTER SEQUENCE dates_id_seq RESTART WITH 1")

for row in dates_list:
    db.execute("INSERT INTO dates (year) VALUES (:year)", {
        "year": row["year"]})


books_list = db.execute(
    "SELECT books_id_t1, isbn, title, authors_id_t1, t2.id dates_id_t2 FROM (SELECT books.id books_id_t1, isbn, title, year, authors.id authors_id_t1 FROM books LEFT JOIN authors ON authors.name = books.author) t1 LEFT JOIN dates t2 ON t2.year = t1.year").fetchall()


db.execute(
    "DELETE FROM books; ALTER TABLE books DROP COLUMN author, DROP COLUMN year, ADD COLUMN author_id INTEGER REFERENCES authors, ADD COLUMN date_id INTEGER REFERENCES dates; ALTER SEQUENCE books_id_seq RESTART WITH 1")

for row in books_list:
    db.execute("INSERT INTO books (id, isbn, title, author_id, date_id) VALUES (:id, :isbn, :title, :author_id, :date_id)", {
        "id": row["books_id_t1"], "isbn": row["isbn"], "title": row["title"], "author_id": row["authors_id_t1"], "date_id": row["dates_id_t2"]})

db.commit()

for row in books_list:
    print(row)
