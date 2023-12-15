from flask import Flask, render_template, request, redirect, flash
from flask_mysqldb import MySQL
import requests,datetime
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# configure db

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD']='anshita@123'
app.config['MYSQL_DB'] = 'login_flask'

mysql = MySQL(app) 
@app.route('/import_books',methods=['GET','POST'])
def import_books():
    # Fetch data from the API
    if request.method =="POST":
        url = "https://frappe.io/api/method/frappe-library"
        param={'page':1,}

        # Get parameters from the form
        title = request.form.get('title')
        authors = request.form.get('authors')
        isbn = request.form.get('isbn')
        publisher = request.form.get('publisher')
        page = request.form.get('page')

        if title:
            param['title'] = title
        if authors:
            param['authors'] = authors
        if isbn:
            param['isbn'] = isbn
        if publisher:
            param['publisher'] = publisher
        if page:
            param['page'] = page

        
        book_count=request.form['import']
        stock= request.form['stock']
        books=0
        print(book_count)
        while books<int(book_count):
            response = requests.get(url,params=param)
            data = response.json().get('message',[])
        
            for item in data:
                try:
                    raw_date = item.get('publication_date')
                    formatted_date = datetime.strptime(raw_date, '%m/%d/%Y').strftime('%Y-%m-%d')
                except ValueError:
                    print(f"Error: Incorrect date format for {raw_date}. Skipping this entry.")
                    continue 

                cursor = mysql.connection.cursor()
                result=cursor.execute('select * from BOOKS where bookID=%s',(item.get('bookID'),))
                if result>0:
                    pass
                else:

                    book_data = (
                        item.get('bookID'),
                        item.get('title'),
                        item.get('authors'),
                        item.get('average_rating'),
                        item.get('isbn'),
                        item.get('isbn13'),
                        item.get('language_code'),
                        item.get(' num_pages'),
                        item.get('ratings_count'),
                        item.get('text_reviews_count'),
                        formatted_date,
                        item.get('publisher'),
                        stock
                    )
                    
                    query = """
                        INSERT INTO BOOKS
                        (bookID, title, authors, average_rating, isbn, isbn13, language_code, num_pages,
                        ratings_count, text_reviews_count, publication_date, publisher, Stock)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(query, book_data)
                    mysql.connection.commit()  
                    
                    print("Data inserted into the database successfully")
                    print(f'{books} imported')
                    if 'conn' in locals() and mysql.connection.is_connected():
                        cursor.close()
                        mysql.connection.close()
                        print("MySQL connection is closed")
                    books+=1
                    if books==int(book_count):
                        break
            param['page']+=1
        flash('BOOK IMPORTED SUCCESSFULLY','success')  
        return redirect('/DATA')
    return render_template('importform.html')



@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route("/form",methods=['GET','POST'])
def index():
    if request.method == 'POST':
        # fetch form data
        userDetails = request.form
        bookID = userDetails['bookID']
        title = userDetails['title']
        authors = userDetails['authors']
        average_rating = userDetails['average_rating']
        isbn = userDetails['isbn']
        isbn13 =userDetails['isbn13']
        language_code = userDetails['language_code']
        num_pages = userDetails['num_pages']
        ratings_count = userDetails['ratings_count']
        text_reviews_count = userDetails['text_reviews_count']
        publication_date = userDetails['publication_date']
        publisher = userDetails['publisher']
        Stock = userDetails['Stock']

        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO BOOKS(bookID, title, authors, average_rating, isbn, isbn13, language_code, num_pages, ratings_count, text_reviews_count, publication_date, publisher,Stock) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(bookID, title, authors, average_rating, isbn, isbn13, language_code, num_pages, ratings_count, text_reviews_count, publication_date, publisher, Stock))
        mysql.connection.commit()
        cur.close()
        return redirect('/BOOKS')
    return render_template('book_form.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form['search']
        cur = mysql.connection.cursor()
        result=cur.execute("SELECT * FROM BOOKS WHERE title LIKE %s OR authors LIKE %s",
                    ('%' + search_query + '%', '%' + search_query + '%'))
        userDetails = cur.fetchall()
        cur.close()
        if result>0:
            return render_template('books.html', userDetails=userDetails)
        else:
            flash('No results found for your search.', 'info')
            return redirect('/')
        
@app.route("/DATA",methods=['GET','POST'])
def data():
    cur = mysql.connection.cursor()
    resultValue = cur.execute('SELECT * FROM BOOKS')
    if resultValue > 0:
        userDetails = cur.fetchall()
        return render_template('books.html',userDetails = userDetails)
    return 'OOPS! Empty Table'

@app.route("/details/<int:book_id>")
def details(book_id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM BOOKS WHERE bookID = %s", (book_id,))
    userDetails = cur.fetchone()  # Fetches the first row that matches the book_id

    cur.close()

    if userDetails:
        return render_template('book_details.html', userDetails=userDetails)
    else:
        return "Book details not found"


@app.route('/delete/<string:sno>', methods=['GET','POST','DELETE'])
def delete(sno):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM BOOKS WHERE bookID = %s', (sno,))
    mysql.connection.commit()
    cur.close()
    flash('Item deleted successfully', 'success')
    return redirect('/DATA')  

@app.route('/update/<int:bookID>',methods=['POST','GET'])
def update(bookID):
    cur=mysql.connection.cursor()
    cur.execute('select * from BOOKS where bookID=%s',(bookID,))
    userDetails=cur.fetchone()
    if request.method == 'POST':
        bookID =request.form['bookID']
        title = request.form['title']
        authors =request.form['authors']
        average_rating = request.form['average_rating']
        isbn = request.form['isbn']
        isbn13 =request.form['isbn13']
        language_code = request.form['language_code']
        num_pages = request.form['num_pages']
        ratings_count = request.form['ratings_count']
        text_reviews_count = request.form['text_reviews_count']
        publication_date = request.form['publication_date']
        publisher = request.form['publisher']
        Stock = request.form['Stock']
        cur = mysql.connection.cursor()
        cur.execute("""
               UPDATE BOOKS
               SET bookID=%s, title=%s, authors=%s, average_rating=%s, isbn=%s, isbn13=%s, language_code=%s, num_pages=%s, ratings_count=%s, text_reviews_count=%s, publication_date=%s, publisher=%s, Stock=%s
               WHERE bookID=%s
            """, (bookID, title, authors, average_rating, isbn, isbn13, language_code, num_pages, ratings_count, text_reviews_count, publication_date, publisher,Stock,bookID))
        # flash("Data Updated Successfully")
        mysql.connection.commit()
        flash('Item updated successfully', 'success')
        return redirect('/DATA')
    return render_template('book_update.html',row=userDetails)


# MEMBER

@app.route('/s_form',methods=['GET','POST'])
def s_form():
    if request.method == 'POST':
        studentDetails = request.form
        Name = studentDetails['name']
        Email = studentDetails['email']
        phone_number = studentDetails['phone_number']
        
        curr = mysql.connection.cursor()
        curr.execute('INSERT INTO MEMBERS(name, email, phone_number) VALUES(%s,%s,%s)',( Name, Email, phone_number))
        mysql.connection.commit()
        curr.close()
        return redirect('/s_data')
    return render_template('MemberForm.html')

@app.route('/s_data',methods = ['GET','POST'])
def students_data():
    curr = mysql.connection.cursor()
    result = curr.execute('select * from MEMBERS')
    if result>0:
        studentDetails = curr.fetchall()

        updated_student_details = []
        for student_tuple in studentDetails:
            student = {
                'ID': student_tuple[0],  
                'Name': student_tuple[1],
                'Email': student_tuple[2],  
                'phone_number': student_tuple[3],
                'book_borrowed': student_tuple[4]  
            }
            student_id = student['ID']
            curr.execute('SELECT * FROM TRANSACTION WHERE student_id = %s', (student_id,))
        mysql.connection.commit()
        flash('Member added successfully!', 'success')
        return render_template('MemberData.html',studentDetails=studentDetails)
    flash('OOPS! Empty Table','error')
    return redirect('welcome.html')

@app.route('/s_update/<int:id>',methods = ['POST','GET'])
def s_update(id):
    curr = mysql.connection.cursor()
    curr.execute('SELECT * FROM MEMBERS where id=%s',(id,))
    studentDetails = curr.fetchone()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        curr.execute("UPDATE MEMBERS SET name=%s, email=%s, phone_number=%s WHERE id=%s", (name, email, phone_number, id))
        mysql.connection.commit()
        curr.close()
        flash('Member updated successfully', 'success')
        return redirect('/s_data')
    return render_template('MemberUpdate.html',r=studentDetails)

@app.route('/s_delete/<string:sno>', methods=['GET','POST'])
def s_delete(sno):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM MEMBERS WHERE id = %s', (sno,))
    mysql.connection.commit()
    cur.close()
    flash('Member deleted successfully', 'success')
    return redirect('/s_data')

#Transaction

@app.route('/t_form',methods=['GET','POST'])
def issueform():
    if request.method == 'POST':    
        transactionDetails = request.form
        student_id = transactionDetails['student_id']
        book_id = transactionDetails['book_id']
        issue_on = transactionDetails['issue_on']
        return_date = transactionDetails['return_date']
        days = transactionDetails['days']
        if int(days)>10:
            penalty = (int(days)-10)*10
            print(penalty)
        penalty=0
        status = transactionDetails['status']
        cur = mysql.connection.cursor()

        # insert book
        result=cur.execute('SELECT Stock FROM BOOKS WHERE bookID=%s',(book_id,))
        result_stock = cur.fetchone()

        if result is not None and result_stock is not None and result_stock[0] > 0:
            cur.execute("UPDATE BOOKS SET Stock = Stock - 1 WHERE bookID = %s", (book_id,))
            cur.execute('INSERT INTO TRANSACTION(student_id,book_id,issue_on,return_date,penalty,status) VALUES(%s,%s,%s,%s,%s,%s)',(student_id,book_id,issue_on,return_date,penalty,status))
            cur.execute('UPDATE MEMBERS SET book_borrowed = book_borrowed + 1 WHERE id = %s', (student_id,))
            mysql.connection.commit()
            # cur.close()
            flash('Book issued successfully','success')
            return redirect('/t_data')
        else:
            cur.close()
            return 'Book not available or out of stock'

    return render_template('issueform.html')

@app.route('/issuebookform',methods=['GET','POST'])
def issuebookform():
    book_id = request.args.get('book_id')
    return render_template('issuebookform.html', book_id=book_id)



@app.route('/t_data',methods = ['GET','POST'])
def t_data():
    curr = mysql.connection.cursor()
    result = curr.execute('select * from TRANSACTION')
    if result>0:
        transactionDetails = curr.fetchall()
        return render_template('issuebookdata.html',transactionDetails=transactionDetails)
    return 'OOPS! Empty Table'


@app.route('/t_delete/<string:sno>', methods=['GET','POST'])
def t_delete(sno):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM TRANSACTION WHERE issue_id = %s', (sno,))
    mysql.connection.commit()
    cur.close()
    flash('Item deleted successfully', 'success')
    return redirect('/t_data')

@app.route('/t_update/<int:issue_id>',methods = ['POST','GET'])
def t_update(issue_id):
    curr = mysql.connection.cursor()
    curr.execute('SELECT * FROM TRANSACTION where issue_id=%s',(issue_id,))
    transactionDetails = curr.fetchone()
    if request.method == 'POST':
        issue_id = request.form['issue_id']
        student_id = request.form['student_id']
        book_id = request.form['book_id']
        issue_on= request.form['issue_on']
        return_date = request.form['return_date']
        penalty = request.form['penalty']
        status = request.form['status']
        curr.execute("UPDATE TRANSACTION SET student_id=%s, book_id=%s, issue_on=%s, return_date=%s, penalty=%s, status=%s WHERE issue_id=%s", (student_id, book_id, issue_on, return_date, penalty, status, issue_id))
        flash("Data Updated Successfully","success")
        mysql.connection.commit()
        curr.close()
        return redirect('/t_data')
    return render_template('issueupdate.html',r=transactionDetails)

@app.route('/returnform',methods=['GET','POST'])
def issue():
    if request.method == 'POST':
        transaction_details = request.form
        issue_id = transaction_details['issue_id']
        bookID = transaction_details['bookID']
        amount = int(transaction_details['amount'])  # Convert amount to an integer
        
        cur = mysql.connection.cursor()

        cur.execute('SELECT penalty FROM TRANSACTION WHERE issue_id = %s', (issue_id,))
        penalty = cur.fetchone()

        if penalty:
            penalty_value = penalty[0]  # Fetch the penalty value from the result tuple
            p = int(penalty_value) - int(amount)
            
            if p > 500:
                cur.close()
                return "Sorry you can't lend a new book because your Debt is greater than 500"
            elif p > 0:
                cur.execute("UPDATE TRANSACTION SET penalty = %s WHERE issue_id = %s", (p, issue_id,))
            else:
                # Handle the case where penalty becomes zero or negative, possibly set status to 'Cleared' or something similar
                cur.execute('DELETE FROM TRANSACTION WHERE issue_id = %s', (issue_id,))
        else:
            cur.close()

            # Handle the case where no penalty is found for the given issue_id
            return "No penalty found for this issue ID"

        mysql.connection.commit()
        cur.close()
        return redirect('/t_data')

    return render_template('returnform.html')
        

if __name__=="__main__":
    app.secret_key = 'your_secret_key_here'
    app.run(debug=True, port=8000)











