# Project 1
Files:

My project consists of 7 .html files (in the templates folder):

-login.html: This is the page where the form must be filled in with the username and password to login as a user.   

-register.html: In this page you can register on the site if you don't have an account, providing creating a username and a password.

-search.html: It consists of a search bar where you can search for a book by title, author, isbn or year. After submit the search a list of links with all the matches of the search will be shown.

-book.html: This page shows the book information (title, author, year, isbn and book data from the Goodreads website) that was selected on the previous page through the link. It also shows a form in which               the user can provide a raiting and a review about the book. Finally, the reviews with the ratings of other users are shown.

-logout.html: when the user log out, this page shows a dialog box informing the user that the session has been logged out.

-error.html: When a user writes an ISBN in the URL that does not exist, this page is shown informing the user that the page has not been found.

-layout.html: It contains the basic design of the website and is used to extend it in the other HTML files.


Also 2 files .py (in the main folder):

-Application.py: It is the application that interacts with the server, the database and the user.

-import.py: It is the application that reads the books.csv file to build and save 3 (users, books and dates) tables that are related to each other. 


And a file called styles.css (in the static folder) that contains the style for the pages.


Tables:

The project have 5 tables to save information:

-books: It contains the information with the title and ISBN of the books.

-authors: It contains the names of the authors.

-dates: It contains the years of book publications.

-users: It contains the username and the hash of the users who have registered.

-reviews: It contains each review and rating that users have posted, with the date and time of the post.


Website:

When you go to "/" (and if there is no session open), you will be redirected to the login page. Here if you have an account, you can log in and if you do not have an account, you can go to the registration page by clicking on the "Register here" link. If you register, you will be logged in automatically and you will be redirected to "/". On this page you can search for a book by its title, isbn, author or year and then go to the page of a book by clicking one of the links that are displayed once you submit the search. If you are not in "/" and you want to go to this page, you must click on the "Search" button located in the upper right corner. To obtain the JSON file of a book from the Goodreads website, you must go to the URL "/api/isbn". To log out, you must click on the "Log out" button located in the upper left corner.