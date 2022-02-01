from flask import Flask, request, render_template, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_session import Session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import datetime
import config
import mongo_repo


app = Flask(__name__)
app.config['SECRET_KEY'] = config.APP_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_CONNECTION
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SESSION_TYPE'] = 'filesystem'

bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

Session(app)
socketio = SocketIO(app, manage_session=False, allowEIO3=True)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')


class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('chat'))

        return '<h1>Invalid username or password</h1>'

    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        try:
            db.session.commit()
        except Exception as ex:
            return '<h1>' + format(ex) + '</h1>'

        return redirect(url_for('chat'))

    return render_template('signup.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/favicon.ico')
def get_favicon():
    return ''


@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    session['username'] = current_user.username
    session['room'] = "default_room"
    return render_template('chat.html', session=session)


@socketio.on('join', namespace='/chat')
@login_required
def join(message):
    room = session.get('room')
    join_room(room)
    emit('status', {'msg': session.get('username') + ' has entered the room.'}, room=room)

    new_joinee = session.get('sid')
    feed_data = mongo_repo.get_feed()

    feed_emit = []
    for _ in feed_data:
        feed_emit.append({'msg': _['created_at'] + '\t' + _['username'] + ' : ' + _['msg']})

    feed_emit.reverse()
    emit('feed', {'feed': feed_emit}, room=new_joinee)


@socketio.on('text', namespace='/chat')
@login_required
def text(message):
    room = session.get('room')
    curr_time = datetime.datetime.now().strftime("%b %d %Y %H:%M:%S")
    username = session.get('username')

    chat_obj = {
        'msg': message['msg'],
        'created_at': curr_time,
        'username': username
    }

    emit('message', {'msg': curr_time + '\t' + username + ' : ' + message['msg']}, room=room)
    mongo_repo.add_chat_message(chat_obj)


@socketio.on('left', namespace='/chat')
@login_required
def left(message):
    room = session.get('room')
    username = session.get('username')
    leave_room(room)
    session.clear()
    emit('status', {'msg': username + ' has left the room.'}, room=room)


if __name__ == '__main__':
    # context = ssl.SSLContext()
    # context.load_cert_chain("cert.pem", "key.pem")
    # app.run(ssl_context=context)
    app.run()
