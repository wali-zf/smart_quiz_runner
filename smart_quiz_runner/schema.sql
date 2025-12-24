DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS quizzes;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS results;


CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student', 'teacher'))
);


CREATE TABLE quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    creator_id INTEGER NOT NULL,
    FOREIGN KEY (creator_id) REFERENCES users (id)
);



CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    options TEXT NOT NULL, 
    correct_answer TEXT NOT NULL,
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
);


CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    quiz_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
);



INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'teacher');
INSERT INTO users (username, password, role) VALUES ('wali', 'wali123', 'student');
