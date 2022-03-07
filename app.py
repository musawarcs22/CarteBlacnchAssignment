
from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, logout_user, current_user
from flask import request
from flask import session, flash
from flask import redirect
import sqlite3 as sql
from flask_bcrypt import Bcrypt

app = Flask(__name__)
db = SQLAlchemy(app) #creating database instance
bcrypt = Bcrypt(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '@$#$@#$@1223secret2'

login_manager = LoginManager() # This will alow our app and flask to handle things for loging in
login_manager.init_app(app)
login_manager.login_view = "signIn"

@login_manager.user_loader # this call back is used to reload the user object from the user id stored in the session
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    
class Tasklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_title = db.Column(db.String(30), nullable=False, unique=True)
    priority = db.Column(db.String(20), nullable=False)
    labels = db.Column(db.String(500), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)    
    
@app.before_first_request
def create_table():
    db.create_all()


#For to do list view 
@app.route('/listView')
def listView():
    if (session['username']):
        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        
        con = sql.connect("database.db")
        con.row_factory = sql.Row
        user_id = user.id
        print(type(user_id))
        print(user_id)
        cur = con.cursor()
        cur.execute("select * from tasklist WHERE user_id = "+str(user_id))
        
        rows = cur.fetchall(); 
        
        
        return render_template('listView.html',rows = rows)
    else:
        unsuccessful = 'Please Login'
        return render_template('signIn.html', umessage=unsuccessful)
    
    
#For SignIn 
@app.route('/')
@app.route('/signIn', methods=['GET', 'POST'])
def signIn():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username, password)
        if not username or not password:
            flash("Please fill all the feilds.")
        else:
            
            user = User.query.filter_by(username=username).first()
            if user:
                if bcrypt.check_password_hash(user.password, password):
                    login_user(user) #creates the cookie and session and tells app that the user is logged in 
                    session['username'] = username # Storing user name in session variable
                    return redirect(url_for('listView'))
                else:
                    #sending flash messege username or password is incorrrect
                    flash('Username or Password is Incorrect!')
                    return render_template('signIn.html')
            else:
                
                flash('User does not exist')
                return render_template('signIn.html')
 
    return render_template('signIn.html')

#For SignUp
@app.route('/signUp',methods = ['POST', 'GET'])
def signUp():
    if request.method == 'POST':
        try:
            name = request.form['username']
            email = request.form['userEmail']
            password = request.form['password']
            confirmPassword = request.form['confirmPassword']
            if password != confirmPassword:
                flash("Please write same password.")
            else:
                hashedPassword = bcrypt.generate_password_hash(password)
                with sql.connect("database.db") as con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO user (username,email,password) VALUES (?,?,?)",(name,email,hashedPassword) )
                    con.commit()
                    msg = "Record successfully added"
        except:
            con.rollback()
            msg = "error in insert operation"
        
        finally:
            return render_template("result.html",msg = msg)
            con.close()
    else:
        return render_template("signUp.html")
    
@app.route('/logout',methods = ['POST', 'GET'])
def logout():
    if (session['username']):
        logout_user()
        # remove the username from the session if it is there
        session.pop('username', None)
        return redirect(url_for('signIn'))
    else:
        unsuccessful = 'Please Login'
        return render_template('signIn.html', umessage=unsuccessful)
    
#For Adding Tasks
@app.route('/addTask',methods = ['POST', 'GET'])
def addTask():
    if request.method == 'POST':
        username = session.get("username")
        user = User.query.filter_by(username=username).first()
        print("---------------")
        print(user.id)
        print("---------------")
        taskTitle = request.form['taskTitle']
        priority = request.form['priority']
        labels = request.form['labels']
        new_task = Tasklist(task_title = taskTitle, priority = priority, labels = labels, user_id = user.id)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('listView'))

    return redirect(url_for('listView'))


@app.route('/delrecord',methods = ['POST', 'GET'])
#For Deleting Tasks
def delrecord():
    
   task_id = None
   
   if request.method == 'POST' or request.method == 'GET':
      try:
         task_id = request.form['task_id']         
         with sql.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("DELETE FROM taskList WHERE id = "+task_id+"")
            con.commit()
            msg = "Record successfully deleted"
            return redirect(url_for('listView'))
      except:
         con.rollback()
         msg = "error in delete operation"
         return redirect(url_for('listView'))
      finally:
         return redirect(url_for('listView'))
         con.close()

@app.route('/editrecord',methods = ['POST', 'GET'])
#For Deleting Tasks --> Under process :)
def editrecord():
    pass


if __name__ == '__main__':
    app.run(debug=True)