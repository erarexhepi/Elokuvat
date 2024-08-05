from datetime import datetime
from app import db

class Visitor(db.Model):
    __tablename__ = 'visitors'
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    comments = db.relationship('Comment', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user_favorites', lazy=True)
    comment_votes = db.relationship('CommentVote', backref='user_votes', lazy=True)

class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Numeric(2, 1), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    visible = db.Column(db.Boolean, default=True)
    comments = db.relationship('Comment', backref='movie', lazy=True)
    favorites = db.relationship('Favorite', backref='movie_favorites', lazy=True)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    votes = db.relationship('CommentVote', backref='comment', lazy=True)

class Favorite(db.Model):
    __tablename__ = 'favorites'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), primary_key=True)
    user = db.relationship('User', backref=db.backref('user_favorites', cascade='all, delete-orphan'))
    movie = db.relationship('Movie', backref=db.backref('movie_favorites', cascade='all, delete-orphan'))

class CommentVote(db.Model):
    __tablename__ = 'comment_votes'
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vote_type = db.Column(db.Boolean, nullable=False)  # True for like, False for dislike
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('comment_id', 'user_id', name='comment_user_unique'),)
