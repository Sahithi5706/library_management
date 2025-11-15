from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "abc123"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="library_db"
)

# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------
@app.route('/')
def home():
    return render_template('home.html')

# --------------------------------------------------
# LOGIN PAGE
# --------------------------------------------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            session['name'] = user['name']

            if user['role'] == 'student':
                return redirect('/student_dashboard')
            else:
                return redirect('/librarian_dashboard')

        return "Invalid login!"

    return render_template('login.html')

# --------------------------------------------------
# STUDENT DASHBOARD
# --------------------------------------------------
@app.route('/student_dashboard')
def student_dashboard():
    if session.get('role') != "student":
        return redirect('/')

    return render_template('student_dashboard.html', name=session['name'])

# --------------------------------------------------
# STUDENT → VIEW ALL BOOKS (GROUP BY CATEGORY)
# --------------------------------------------------
@app.route('/books')
def books():
    cursor = db.cursor(dictionary=True)
    query = """
        SELECT b.*, c.category_name
        FROM books b
        JOIN categories c ON b.category_id=c.category_id
        ORDER BY c.category_name;
    """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('books.html', books=data)

# --------------------------------------------------
# STUDENT → VIEW BOOKS THEY BORROWED
# --------------------------------------------------
@app.route('/my_books')
def my_books():
    uid = session['user_id']

    cursor = db.cursor(dictionary=True)
    query = """
        SELECT b.title, b.author, bb.borrow_date
        FROM borrowed_books bb
        JOIN books b ON bb.book_id=b.book_id
        WHERE bb.user_id=%s
    """
    cursor.execute(query, (uid,))
    data = cursor.fetchall()
    cursor.close()

    return render_template('my_books.html', data=data)

# --------------------------------------------------
# STUDENT → REQUEST A NEW BOOK
# --------------------------------------------------
@app.route('/request_book', methods=['GET','POST'])
def request_book():
    if request.method == 'POST':
        uid = session['user_id']
        book_title = request.form['title']
        message = request.form['message']

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO requests (user_id, book_title, message) VALUES (%s,%s,%s)",
            (uid, book_title, message)
        )
        db.commit()
        cursor.close()

        return redirect('/student_dashboard')

    return render_template('requests.html')

# --------------------------------------------------
# LIBRARIAN DASHBOARD
# --------------------------------------------------
@app.route('/librarian_dashboard')
def librarian_dashboard():
    if session.get('role') != "librarian":
        return redirect('/')
    return render_template('librarian_dashboard.html')

# --------------------------------------------------
# LIBRARIAN → VIEW ALL STUDENTS & THEIR BORROWED BOOKS
# --------------------------------------------------
@app.route('/manage_borrowed')
def manage_borrowed():
    cursor = db.cursor(dictionary=True)
    query = """
        SELECT bb.borrow_id, u.name, u.user_id, b.title, bb.borrow_date
        FROM borrowed_books bb
        JOIN users u ON bb.user_id = u.user_id
        JOIN books b ON bb.book_id = b.book_id;
    """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()

    return render_template('manage_borrowed.html', data=data)

# --------------------------------------------------
# LIBRARIAN → DELETE BORROWED BOOK ENTRY
# --------------------------------------------------
@app.route('/delete/<int:id>')
def delete_book(id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM borrowed_books WHERE borrow_id=%s", (id,))
    db.commit()
    cursor.close()
    return redirect('/manage_borrowed')

# --------------------------------------------------
# LOGOUT
# --------------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
