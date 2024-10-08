import os
from app import app
from flask import render_template, request, redirect, session, url_for, flash
from sqlalchemy import text
from db import db
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
    
    sql = text(f"""
        SELECT m.id, m.name, m.rating, m.comment, 
               c.id AS comment_id, c.content AS comment_content, 
               u.username AS comment_username, c.created_at AS comment_created_at, 
               (SELECT COUNT(*) FROM comment_votes WHERE comment_id = c.id AND vote_type = TRUE) AS likes,
               (SELECT COUNT(*) FROM comment_votes WHERE comment_id = c.id AND vote_type = FALSE) AS dislikes
        FROM movies m
        LEFT JOIN comments c ON m.id = c.movie_id
        LEFT JOIN users u ON c.user_id = u.id
        WHERE m.visible = TRUE
        ORDER BY {sort_query}, c.created_at
    """)
    
    result = db.session.execute(sql)
    movies_with_comments = {}
    for row in result:
        movie_id = row.id
        if movie_id not in movies_with_comments:
            movies_with_comments[movie_id] = {
                "id": row.id,
                "name": row.name,
                "rating": row.rating,
                "comment": row.comment,
                "comments": []
            }
        if row.comment_id:
            movies_with_comments[movie_id]["comments"].append({
                "id": row.comment_id,
                "content": row.comment_content,
                "username": row.comment_username,
                "created_at": row.comment_created_at,
                "likes": row.likes,
                "dislikes": row.dislikes
            })

    visitor_sql = text("SELECT COUNT(*) FROM visitors")
    visitor_result = db.session.execute(visitor_sql)
    visitor_count = visitor_result.scalar()

    return render_template(
        "index.html", 
        count=len(movies_with_comments), 
        movies=movies_with_comments.values(), 
        sort_by=sort_by, 
        visitor_count=visitor_count
    )

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
        flash("All fields are required.", "error")
        return redirect(url_for("new"))

    try:
        rating = float(rating)
        if rating < 1 or rating > 5:
            flash("Rating must be between 1 and 5.", "error")
            return redirect(url_for("new"))
    except ValueError:
        flash("Invalid rating.", "error")
        return redirect(url_for("new"))

    sql = text("SELECT id, visible FROM movies WHERE name=:name")
    result = db.session.execute(sql, {"name": name})
    existing_movie = result.fetchone()

    if existing_movie:
        if existing_movie.visible:
            flash("Movie already exists. You can interact with the existing movie.", "error")
            return redirect(url_for("new"))
        else:
            sql = text("UPDATE movies SET visible=TRUE, rating=:rating, comment=:comment WHERE id=:id")
            db.session.execute(sql, {"rating": rating, "comment": comment, "id": existing_movie.id})
            db.session.commit()
            flash("Movie re-added with new details.", "success")
            return redirect(url_for("index"))
    else:
        sql = text("INSERT INTO movies (name, rating, comment, visible) VALUES (:name, :rating, :comment, TRUE)")
        db.session.execute(sql, {"name": name, "rating": rating, "comment": comment})
        db.session.commit()
        flash("Movie added successfully.", "success")
        return redirect("/")

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
            return render_template("login.html", error=error, visitor_count=get_visitor_count())
        if len(password) < 3:
            error = 'Password must be at least 3 characters long.'
            return render_template("login.html", error=error, visitor_count=get_visitor_count())

        sql = text("SELECT id, password FROM users WHERE username=:username")
        result = db.session.execute(sql, {"username": username})
        user = result.fetchone()
        if not user:
            error = "Incorrect username."
            return render_template("login.html", error=error, visitor_count=get_visitor_count())
        else:
            hash_value = user.password
            if check_password_hash(hash_value, password):
                session["username"] = username
                session["user_id"] = user.id
                session["csrf_token"] = os.urandom(16).hex() 
                return redirect("/")
            else:
                error = 'Incorrect password.'
                return render_template("login.html", error=error, visitor_count=get_visitor_count())
    return render_template("login.html", visitor_count=get_visitor_count())

def get_visitor_count():
    visitor_sql = text("SELECT COUNT(*) FROM visitors")
    visitor_result = db.session.execute(visitor_sql)
    return visitor_result.scalar()

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

        existing_user_sql = text("SELECT id FROM users WHERE username=:username")
        existing_user = db.session.execute(existing_user_sql, {"username": username}).fetchone()
        if existing_user:
            error = 'Username already exists. Try another username.'
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
    existing_favorite_sql = text("SELECT * FROM favorites WHERE user_id=:user_id AND movie_id=:movie_id")
    existing_favorite = db.session.execute(existing_favorite_sql, {"user_id": user_id, "movie_id": movie_id}).fetchone()

    if existing_favorite:
        return render_template("error.html", message="Favorite already exists")

    sql = text("INSERT INTO favorites (user_id, movie_id) VALUES (:user_id, :movie_id)")
    db.session.execute(sql, {"user_id": user_id, "movie_id": movie_id})
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
    sql = text("DELETE FROM favorites WHERE user_id=:user_id AND movie_id=:movie_id")
    db.session.execute(sql, {"user_id": user_id, "movie_id": movie_id})
    db.session.commit()

    return redirect(url_for("view_favorites"))

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

@app.route("/comment/vote/<int:comment_id>/<vote_type>", methods=["POST"])
def vote_comment(comment_id, vote_type):
    if "username" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    vote_type = True if vote_type == "like" else False

    existing_vote_sql = text("SELECT id FROM comment_votes WHERE comment_id=:comment_id AND user_id=:user_id")
    existing_vote = db.session.execute(existing_vote_sql, {"comment_id": comment_id, "user_id": user_id}).fetchone()

    if existing_vote:
        sql = text("UPDATE comment_votes SET vote_type=:vote_type WHERE comment_id=:comment_id AND user_id=:user_id")
        db.session.execute(sql, {"vote_type": vote_type, "comment_id": comment_id, "user_id": user_id})
    else:
        sql = text("INSERT INTO comment_votes (comment_id, user_id, vote_type, created_at) VALUES (:comment_id, :user_id, :vote_type, NOW())")
        db.session.execute(sql, {"comment_id": comment_id, "user_id": user_id, "vote_type": vote_type})
    db.session.commit()

    return redirect(url_for("index"))
