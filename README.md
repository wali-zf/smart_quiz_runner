=============================================================================

<h1>SMART QUIZ RUNNER</h1>

=============================================================================

<h3>PREREQUISITES</h3>

Before running the application, make sure you have Python installed.
You also need to install the 'flask' library.

Open your terminal (Command Prompt or VS Code Terminal) and run:

pip install flask

<h3>HOW TO RUN</h3>

Open the project folder in VS Code.

Open the Terminal (Ctrl + `).

Type the following command and press Enter:

python app.py

The application will start, and your default web browser should open
automatically to: https://www.google.com/search?q=http://127.0.0.1:5000/

<h3>ACCOUNTS & PASSWORDS</h3>

Use the following default accounts to log in and test the system.

<h4>A. Teacher Account (To create quizzes):</h4>
Username: admin
Password: admin123

<h4>B. Student Account (To take quizzes):</h4>
Username: wali
Password: wali123

Note: If these accounts do not exist in your database yet, click "Register" on
the login page and create them using the credentials above.

<h3>FOLDER STRUCTURE</h3>

Ensure your project folder looks exactly like this:

/smart_quiz_runner
|--- app.py                (The main backend file)
|--- schema.sql            (The database blueprint)
|--- /static
|--- /uploads       (Images uploaded by users will go here)
|--- /templates
|--- login.html
|--- register.html
|--- dashboard.html
|--- create_quiz.html
|--- edit_quiz.html
|--- add_questions.html
|--- take_quiz.html
|--- result.html
|--- quiz_results.html
|--- student_history.html
|--- profile.html

<h3>FEATURES</h3>

This system includes a complete suite of professional assessment tools:

<h4>A. User Management</h4>

Role-based Authentication (Student vs. Teacher).

Profile Management: Update Full Name, Change Password.

Profile Picture Uploads.

<h4>B. Teacher Tools (Quiz Creation)</h4>

Create, Edit, and Delete Quizzes.

Set Time Limits (Countdown Timer).

Set Deadlines (Auto-close quiz after specific date/time).

Set Passing Score (%).

Set Maximum Attempts allowed per student.

"Strict Mode" (Anti-Cheating): Detects if a student switches tabs.

<h4>C. Advanced Question Types</h4>

Multiple Choice (MCQ) with variable options.

True / False questions.

Short Answer (Text) questions with case-insensitive auto-grading.

Image Attachments for questions.

<h4>D. Student Experience</h4>

Real-time Dashboard with Search functionality.

Randomized Questions and Options (prevent cheating).

Immediate Feedback: Score, Percentage, Pass/Fail status.

Detailed Review: See exactly which questions were wrong.

Quiz History tracking.

<h4>E. Analytics & Reporting</h4>

Class Leaderboard for every quiz.

Statistics: Total Attempts, Class Average, Highest Score.

Export Results to CSV (Excel compatible).

<h3>DISCLAIMER</h3>

This project is a result of collaborative teamwork and includes assistance from AI tools. It is not the sole work of a single individual.
