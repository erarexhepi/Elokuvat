import os
from app import app
from flask import render_template, request, redirect, session, url_for, flash
from sqlalchemy import text
from db import db
from models import Movie, Comment, User, Visitor, Favorite, CommentVote
from werkzeug.security import check_password_hash, generate_password_hash
from users import check_csrf

@app.before_request
def before_request():
    if "csrf_token" not in session:
        session["csrf_token"] = os.urandom(16).hex()

    if request.endpoint not in ['login', 'register']:
        if request.method == "POST":
            check_csrf()

    if request.endpoint == 'index':
        visitor_sql = text("INSERT INTO visitors DEFAULT VALUES")
        db.session.execute(visitor_sql)
        db.session.commit()

@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))

    sort_by = request.args.get("sort_by", "name_asc")
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

    movies_with_comments = []
    for movie in movies:
        movie_comments_sql = text("""
            SELECT C.id, C.content, U.username, C.created_at,
                   (SELECT COUNT(*) FROM comment_votes WHERE comment_id=C.id AND vote_type=TRUE) AS likes,
                   (SELECT COUNT(*) FROM comment_votes WHERE comment_id=C.id AND vote_type=FALSE) AS dislikes
            FROM comments C
            JOIN users U ON C.user_id=U.id
            WHERE C.movie_id=:movie_id
            ORDER BY C.created_at
        """)
        movie_comments_result = db.session.execute(movie_comments_sql, {"movie_id": movie.id})
        comments = movie_comments_result.fetchall()
        movie_with_comments = {
            "id": movie.id,
            "name": movie.name,
            "rating": movie.rating,
            "comment": movie.comment,
            "comments": comments
        }
        movies_with_comments.append(movie_with_comments)

    visitor_sql = text("SELECT COUNT(*) FROM visitors")
    visitor_result = db.session.execute(visitor_sql)
    visitor_count = visitor_result.scalar()

    return render_template("index.html", count=len(movies_with_comments), movies=movies_with_comments, sort_by=sort_by, visitor_count=visitor_count)

@app.route("/new")
def new():
    try:
        return render_template("new.html")
    except Exception as e:
        print(f"Error occurred: {e}")
        return render_template("error.html", message="An error occurred while loading the page.")

@app.route("/send", methods=["POST"])
def send():
    check_csrf()
    name = request.form["name"].strip()
    rating = request.form["rating"]
    comment = request.form["comment"].strip()
    
    if not name or not rating or not comment:
        flash("All fields are required.")
        return redirect(url_for("new"))

    try:
        rating = float(rating)
        if rating < 1 or rating > 5:
            flash("Rating must be between 1 and 5.")
            return redirect(url_for("new"))
    except ValueError:
        flash("Invalid rating.")
        return redirect(url_for("new"))

    existing_movie = Movie.query.filter_by(name=name).first()
    if existing_movie:
        flash("Movie already exists. You can interact with the existing movie.")
        return redirect(url_for("index"))

    movie = Movie(name=name, rating=rating, comment=comment, visible=True)
    db.session.add(movie)
    db.session.commit()
    return redirect("/")

@app.route("/comment/<int:movie_id>", methods=["POST"])
def comment(movie_id):
    check_csrf()
    if "username" not in session:
        return redirect(url_for("index"))

    content = request.form["content"].strip()
    username = session["username"]

    if not content:
        return render_template("error.html", message="Comment cannot be empty")

    user_sql = text("SELECT id FROM users WHERE username=:username")
    user_result = db.session.execute(user_sql, {"username": username})
    user = user_result.fetchone()
    if not user:
        return render_template("error.html", message="User not found")

    user_id = user.id

    sql = text("INSERT INTO comments (movie_id, user_id, content, created_at) VALUES (:movie_id, :user_id, :content, NOW())")
    db.session.execute(sql, {"movie_id": movie_id, "user_id": user_id, "content": content})
    db.session.commit()

    return redirect(url_for("index"))

@app.route("/delete_comment/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id):
    check_csrf()
    if "username" not in session:
        return redirect(url_for("index"))

    username = session["username"]

    user_sql = text("SELECT id FROM users WHERE username=:username")
    user_result = db.session.execute(user_sql, {"username": username})
    user = user_result.fetchone()
    if not user:
        return render_template("error.html", message="User not found")

    user_id = user.id

    comment_sql = text("SELECT id FROM comments WHERE id=:comment_id AND user_id=:user_id")
    comment_result = db.session.execute(comment_sql, {"comment_id": comment_id, "user_id": user_id})
    comment = comment_result.fetchone()
    if not comment:
        return render_template("error.html", message="Comment not found or you do not have permission to delete this comment")

    sql = text("DELETE FROM comments WHERE id=:comment_id AND user_id=:user_id")
    db.session.execute(sql, {"comment_id": comment_id, "user_id": user_id})
    db.session.commit()

    return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if len(username) < 3:
            error = 'Username must be at least 3 characters long.'
            return render_template("login.html", error=error)
        if len(password) < 3:
            error = 'Password must be at least 3 characters long.'
            return render_template("login.html", error=error)

        sql = text("SELECT id, password FROM users WHERE username=:username")
        result = db.session.execute(sql, {"username": username})
        user = result.fetchone()
        if not user:
            error = "Incorrect username."
            return render_template("login.html", error=error)
        else:
            hash_value = user.password
            if check_password_hash(hash_value, password):
                session["username"] = username
                session["user_id"] = user.id
                session["csrf_token"] = os.urandom(16).hex() 
                return redirect("/")
            else:
                error = 'Incorrect password.'
                return render_template("login.html", error=error)
    return render_template("login.html")


@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        password_again = request.form["password_again"]

        if len(username) < 3:
            error = 'Username must be at least 3 characters long.'
            return render_template("register.html", error=error)
        if len(password) < 3:
            error = 'Password must be at least 3 characters long.'
            return render_template("register.html", error=error)

        if password == password_again:
            hash_value = generate_password_hash(password)
            sql = text("INSERT INTO users (username, password) VALUES (:username, :password)")
            db.session.execute(sql, {"username": username, "password": hash_value})
            db.session.commit()
            return redirect("/")
        else:
            error = 'Passwords do not match.'
            return render_template("register.html", error=error)
    return render_template("register.html")

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    sql = text("UPDATE movies SET visible=FALSE WHERE id=:id")
    db.session.execute(sql, {"id": id})
    db.session.commit()
    return redirect("/")

@app.route("/result", methods=["GET"])
def result():
    query = request.args.get("query", "")
    if not query:
        return render_template("result.html", messages=[])

    sql = text("SELECT id, name, rating, comment FROM movies WHERE visible=TRUE AND (name ILIKE :query OR comment ILIKE :query)")
    result = db.session.execute(sql, {"query": f"%{query}%"})
    movies = result.fetchall()

    messages = []
    for movie in movies:
        messages.append({
            "id": movie.id,
            "name": movie.name,
            "rating": movie.rating,
            "comment": movie.comment
        })

    return render_template("result.html", messages=messages)

@app.route("/favorites", methods=["GET"])
def view_favorites():
    if "username" not in session:
        return redirect(url_for("login"))
    
    username = session["username"]
    user_sql = text("SELECT id FROM users WHERE username=:username")
    user_result = db.session.execute(user_sql, {"username": username})
    user = user_result.fetchone()

    if not user:
        return render_template("error.html", message="User not found")

    user_id = user.id
    favorites_sql = text("""
        SELECT m.id, m.name, m.rating, m.comment
        FROM movies m
        JOIN favorites f ON m.id = f.movie_id
        WHERE f.user_id = :user_id AND m.visible = TRUE
    """)
    result = db.session.execute(favorites_sql, {"user_id": user_id})
    favorite_movies = result.fetchall()

    return render_template("favorites.html", movies=favorite_movies)

@app.route("/add_favorite/<int:movie_id>", methods=["POST"])
def add_favorite(movie_id):
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    user_sql = text("SELECT id FROM users WHERE username=:username")
    user_result = db.session.execute(user_sql, {"username": username})
    user = user_result.fetchone()

    if not user:
        return render_template("error.html", message="User not found")

    user_id = user.id
    existing_favorite = Favorite.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if existing_favorite:
        return render_template("error.html", message="Favorite already exists")

    favorite = Favorite(user_id=user_id, movie_id=movie_id)
    db.session.add(favorite)
    db.session.commit()

    return redirect(url_for("view_favorites"))

@app.route("/remove_favorite/<int:movie_id>", methods=["POST"])
def remove_favorite(movie_id):
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    user_sql = text("SELECT id FROM users WHERE username=:username")
    user_result = db.session.execute(user_sql, {"username": username})
    user = user_result.fetchone()

    if not user:
        return render_template("error.html", message="User not found")

    user_id = user.id

    favorite = Favorite.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()

    return redirect(url_for("view_favorites"))

@app.route("/comment/vote/<int:comment_id>/<vote_type>", methods=["POST"])
def vote_comment(comment_id, vote_type):
    if "username" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    vote_type = True if vote_type == "like" else False

    existing_vote = CommentVote.query.filter_by(comment_id=comment_id, user_id=user_id).first()
    if existing_vote:
        existing_vote.vote_type = vote_type
        db.session.commit()
    else:
        vote = CommentVote(comment_id=comment_id, user_id=user_id, vote_type=vote_type)
        db.session.add(vote)
        db.session.commit()

    return redirect(url_for("index"))
