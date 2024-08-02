from flask import Flask, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://rexera:MoiMoi123@localhost/sovellus"
app.secret_key = getenv("SECRET_KEY")

db = SQLAlchemy(app)

@app.before_request
def before_request():
    if request.endpoint == 'index':
        visitor_sql = text("INSERT INTO visitors DEFAULT VALUES")
        db.session.execute(visitor_sql)
        db.session.commit()

@app.route("/")
def index():
    sort_by = request.args.get("sort_by", "name_asc")  # A-Z
    sort_query = "name ASC"

    if sort_by == "rating_desc":
        sort_query = "rating DESC"
    elif sort_by == "rating_asc":
        sort_query = "rating ASC"
    elif sort_by == "name_asc":
        sort_query = "name ASC"

    sql = text(f"SELECT id, name, rating, comment FROM movies WHERE visible=TRUE ORDER BY {sort_query}")
    result = db.session.execute(sql)
    movies = result.fetchall()
    visitor_sql = text("SELECT COUNT(*) FROM visitors")
    visitor_result = db.session.execute(visitor_sql)
    visitor_count = visitor_result.scalar()

    return render_template("index.html", count=len(movies), movies=movies, sort_by=sort_by, visitor_count=visitor_count)

@app.route("/new")
def new():
    return render_template("new.html")

@app.route("/send", methods=["POST"])
def send():
    name = request.form["name"]
    rating = request.form["rating"]
    comment = request.form["comment"]
    sql = text("INSERT INTO movies (name, rating, comment) VALUES (:name, :rating, :comment)")
    db.session.execute(sql, {"name": name, "rating": rating, "comment": comment})
    db.session.commit()
    return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    sql = text("SELECT id, password FROM users WHERE username=:username")
    result = db.session.execute(sql, {"username": username})
    user = result.fetchone()
    if not user:
        error = "Incorrect username."
        return render_template("index.html", error=error)
    else:
        hash_value = user.password
        if check_password_hash(hash_value, password):
            session["username"] = username
            return redirect("/")
        else:
            error = 'Incorrect password.'
            return render_template("index.html", error=error)

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

@app.route("/result")
def result():
    query = request.args.get("query", "")
    sql = text("SELECT id, name, rating, comment FROM movies WHERE (name LIKE :query OR comment LIKE :query) AND visible=TRUE")
    result = db.session.execute(sql, {"query": f"%{query}%"})
    messages = result.fetchall()
    return render_template("result.html", messages=messages)

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/add_user", methods=['POST'])
def add_user():
    username = request.form["username"]
    password = request.form["password"]
    password_again = request.form['password_again']
    if password == password_again:
        hash_value = generate_password_hash(password)
        sql = text("INSERT INTO users (username, password) VALUES (:username, :password)")
        db.session.execute(sql, {"username": username, "password": hash_value})
        db.session.commit()
        return redirect("/")
    else:
        error = 'Passwords do not match.'
        return render_template("register.html", error=error)

@app.route("/delete/<int:id>")
def delete(id):
    sql = text("UPDATE movies SET visible=FALSE WHERE id=:id")
    db.session.execute(sql, {"id": id})
    db.session.commit()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
