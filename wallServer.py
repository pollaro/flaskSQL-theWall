from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import re,os,md5,binascii
app = Flask(__name__)
app.secret_key = os.urandom(32)
nameRegex = r'^\w{2,}'
nameRegex = re.compile(nameRegex)
emailRegex = r"^\w+@\w+\.[a-z]{3}"
emailRegex = re.compile(emailRegex)
mysql = MySQLConnector(app,'theWall')


@app.route('/')
def indexPage():
    return render_template('login.html')

@app.route('/register',methods=['POST'])
def register():
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    emailAdd = request.form['emailAdd']
    passWord = request.form['passWord']
    passConf = request.form['passConf']
    error = False
    if not nameRegex.match(firstName):
        flash('First Name may not be empty','firstError')
        error = True
    if not nameRegex.match(lastName):
        flash("Last Name may not be empty",'lastError')
        error = True
    if not emailRegex.match(emailAdd):
        flash("Invalid email address",'emailError')
        error = True
    if len(passWord) < 8:
        flash("Password must be AT LEAST 8 characters",'passShort')
        error = True
    if passWord != passConf:
        flash("Password and Confirm Password must be the same",'passMatch')
        error = True18pt
    if error:
        return redirect('/')
    else:
        # salt = binascii.b2a_hex(os.urandom(15))
        hashed_pw = md5.new(passWord).hexdigest()
        query = 'SELECT * FROM users WHERE email = :emailAdd'
        data = {'emailAdd': emailAdd}
        emailCheck = mysql.query_db(query,data)
        if not emailCheck:
            query = 'INSERT INTO users (first_name,last_name,email,password,created_at,updated_at) VALUES (:firstName,:lastName,:emailAdd,:passWord,NOW(),NOW())'
            data = {'firstName':firstName,'lastName':lastName,'emailAdd':emailAdd,'passWord':hashed_pw}
            mysql.query_db(query,data)
            session['firstName'] = firstName
            session['lastName'] = lastName
            query = 'SELECT id FROM users WHERE email = :emailAdd'
            data = {'emailAdd':emailAdd}
            newid = mysql.query_db(query,data)
            session['id'] = newid[0]['id']
            return redirect('/wall')
        else:
            flash("Email already registered",'emailInUse')
            return redirect('/')

@app.route('/login',methods=['POST'])
def login():
    emailLog = request.form['emailLog']
    passLog = request.form['passLog']
    if len(passLog) == 0:
        flash('Password is required','noPass')
        return redirect('/')
    if not emailRegex.match(emailLog):
        flash('That is not a valid email','loginEmail')
        return redirect('/')
    query = 'SELECT * FROM users WHERE email = :emailLog'
    data = {'emailLog':emailLog}
    loginData = mysql.query_db(query,data)
    if (emailLog == loginData[0]['email'] and md5.new(passLog).hexdigest() == loginData[0]['password']):
        session['firstName'] = loginData[0]['first_name']
        session['lastName'] = loginData[0]['last_name']
        session['id'] = loginData[0]['id']
        query = 'UPDATE users SET updated_at = NOW()'
        mysql.query_db(query)
        return redirect('/wall')
    else:
        flash('Email or Pass are not found or do not match in database','loginError')
        return redirect('/')

@app.route('/postMessage',methods=['POST'])
def postMessage():
    messageIn = request.form['newMessage']
    messageUserId = session['id']
    query = 'INSERT INTO messages (user_id,message,created_at,updated_at) VALUES (:messageUserId,:messageIn,NOW(),NOW())'
    data = {'messageIn':messageIn,'messageUserId':messageUserId}
    mysql.query_db(query,data)
    return redirect('/wall')

@app.route('/postComment',methods=['POST'])
def postComment():
    commentIn = request.form['newComment']
    messageID = request.form['messageID']
    commentUserId = session['id']
    query = 'INSERT INTO comments (user_id,message_id,comment,created_at,updated_at) VALUES (:commentUserId,:messageID,:commentIn,NOW(),NOW())'
    data = {'commentIn':commentIn,'commentUserId':commentUserId,'messageID':messageID}
    mysql.query_db(query,data)
    return redirect('/wall')

@app.route('/wall')
def wall():
    query = 'SELECT user_id,messages.id,first_name,last_name,message,messages.created_at FROM messages LEFT JOIN users ON messages.user_id = users.id ORDER BY created_at DESC'
    messages = mysql.query_db(query)
    query = 'SELECT user_id,message_id,comments.id,first_name,last_name,comment,comments.created_at FROM comments LEFT JOIN users ON comments.user_id = users.id ORDER BY message_id ASC,created_at ASC'
    comments = mysql.query_db(query)
    return render_template('wall.html',messages=messages,comments=comments)

@app.route('/logout',methods=['POST'])
def logout():
    session.clear()
    return redirect('/')
app.run(debug=True)
