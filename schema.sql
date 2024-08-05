CREATE TABLE visitors (
    id SERIAL PRIMARY KEY,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE movies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    rating DECIMAL(2, 1) NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    visible BOOLEAN DEFAULT TRUE
);

CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    movie_id INTEGER NOT NULL REFERENCES movies(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE favorites (
    user_id INTEGER NOT NULL REFERENCES users(id),
    movie_id INTEGER NOT NULL REFERENCES movies(id),
    PRIMARY KEY (user_id, movie_id)
);

CREATE TABLE comment_votes (
    id SERIAL PRIMARY KEY,
    comment_id INTEGER NOT NULL REFERENCES comments(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    vote_type BOOLEAN NOT NULL, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT comment_user_unique UNIQUE (comment_id, user_id)
);
