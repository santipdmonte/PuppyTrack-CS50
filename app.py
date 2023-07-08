import os

from flask import Flask, flash, redirect, render_template, request, session, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from functools import wraps
import json
import requests
from flask_session import Session
import datetime

app = Flask(__name__)

app.secret_key = 'your_secret_key'

# # Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"
# app.config['SESSION_COOKIE_NAME'] = 'nuevo_nombre_de_cookie'
# Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///puppytrack.db")

# def login_required(f):
#     """
#     Decorate routes to require login.

#     https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
#     """
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if session.get("user_id") is None:
#             return redirect("/login")
#         return f(*args, **kwargs)
#     return decorated_function



@app.route('/')
def index():
    session['username'] = 'John'
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        password = request.form.get("password")
        confirmation = request.form.get('confirmation')
        if password is not None:
            password_hash = generate_password_hash(password)
        username = request.form.get("username")

        # Validate if the username is not null
        if not username or not password or not confirmation:
            return apology('Empty files')

        # Validate if the username already exists
        existing_user = db.execute("SELECT * FROM users WHERE username = ? LIMIT 1", username)
        if existing_user:
            return apology('Username in use')
        if password != confirmation:
            return apology('Password does not match')
        db.execute("INSERT INTO users (username, hash) VALUES (?,?)", username, password_hash)

        # Validate the sesion register
        user = db.execute("SELECT * FROM users WHERE username = ? LIMIT 1", username)
        if user:
            # Remember which user has logged in
            session["user_id"] = user[0]["id"]
            # Redirect user to home page
            response = make_response('OK')
            response.status_code = 200
            return redirect("/")
        else:
            return apology("Error to register", 403)

    else:
        return render_template("register.html")


@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']
        return f'Logged in as {username}'
    else:
        return 'Not logged in'




@app.route('/vet', methods=["GET", "POST"])
# @login_required
def vet():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        try:
            total_price = 0 #Total price for the consult
            data = request.get_json()
            # Data[0] are the client data
            client = data[0]
            db.execute("BEGIN;")
            db.execute("INSERT INTO consult_index(name, consult_observation, date_time, status) VALUES (?,?,?,?)", client['name'], client['observation'], datetime.datetime.now(), 'active')
            id = db.execute("SELECT id from consult_index ORDER BY id DESC LIMIT 1")[0]
            # Data[1]+ are the service data
            for d in data[1:]:
                total_price = total_price + int(d['price'])
                db.execute("INSERT INTO consult_services(amount, treatment_pharma, observation, price, consult_id) VALUES(?,?,?,?,?)",d['amount'],d['pharma'],d['observation'],d['price'],id['id'])
            db.execute("UPDATE consult_index SET total_price = ? WHERE id = ?", total_price, id['id'])
            db.execute("END;")

        except:
            print("Error decoding JSON")

        services = db.execute("SELECT * FROM services")
        return render_template("vet.html",services=services)
    # User reached route via GET
    else:
        services = db.execute("SELECT * FROM services")
        return render_template("vet.html",services=services)


@app.route('/front', methods=["GET", "POST"])
# @login_required
def front():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        db.execute("UPDATE consult_index set status = 'desactive' WHERE id = ? ",request.form.get("consult_id"))
        consults = db.execute("SELECT * FROM consult_index WHERE status = 'active' ")
        services = []
        for c in consults:
            services = services + db.execute("SELECT * FROM consult_services WHERE consult_id  = ? ",c['id'])
        return render_template("front.html", consults = consults, services = services)
    consults = db.execute("SELECT * FROM consult_index WHERE status = 'active' ")
    services = []
    for c in consults:
        services = services + db.execute("SELECT * FROM consult_services WHERE consult_id  = ? ",c['id'])
    return render_template("front.html", consults = consults, services = services)

if __name__ == '__main__':
    app.run()