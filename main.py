from flask import Flask, render_template, url_for, flash, redirect
from forms import RegistrationForm
from flask_sqlalchemy import SQLAlchemy
from audio import printWAV
import time, random, threading
from turbo_flask import Turbo
from flask_bcrypt import Bcrypt
from flask_behind_proxy import FlaskBehindProxy
from sqlalchemy.exc import IntegrityError
from flask_caching import Cache

config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}


app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)
proxied = FlaskBehindProxy(app)
# app.config['SECRET_KEY'] = '17e81666b51cd4989ff8a76af64ba52a'
app.config['SECRET_KEY'] = '10364988612687b4f1a2b1cbba9a2243'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
interval=10
FILE_NAME = "poem.wav"
turbo = Turbo(app)

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(20), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password = db.Column(db.String(60), nullable=False)
  


  def __repr__(self):
    return f"User('{self.username}', '{self.email}')"
  
@app.route("/")
@app.route("/index")
@cache.cached(timeout=50)
def index():
     return render_template('index.html')
#      return 'Cached for 50s'
  
@app.route("/home")
@app.route("/")
def home():
    return render_template('home.html', subtitle='Home Page', text='This is the home page')
    
@app.route("/second_page")
def second_page():
    return render_template('second_page.html', subtitle='Second Page', text='This is the second page')
  
@app.route("/about")
def about():
    return render_template('about.html', subtitle='About', text='This is the about page')

# @cache.cached(timeout=50, key_prefix='register')
@app.route("/register", methods=['GET', 'POST'])
def register():
  form = RegistrationForm()
  if form.validate_on_submit(): # checks if entries are valid
    try:
      user_password = form.password.data
      pw_hash = bcrypt.generate_password_hash(user_password)
      print(pw_hash)
      user = User(username=form.username.data, email=form.email.data, password=form.password.data)
      db.session.add(user)
      db.session.commit()
    except IntegrityError:
      flash(f'Cannot create account with the given username.')
      return redirect(url_for('home')) # if so - send to home page
    else:
      flash(f'Account created for {form.username.data}!', 'success')
      return redirect(url_for('home')) # if so - send to home page
  return render_template('register.html', title='Register', form=form)  
# cached_register = register()

@app.route("/captions")
def captions():
    TITLE = "Test_Audio"
#     FILE_NAME = "examples_english.wav"
    return render_template('captions.html', songName=TITLE, file=FILE_NAME)
@app.before_first_request
def before_first_request():
    #resetting time stamp file to 0
    file = open("pos.txt","w") 
    file.write(str(0))
    file.close()

    #starting thread that will time updates
    threading.Thread(target=update_captions, daemon=True).start()

@app.context_processor
def inject_load():
#     pos = None
    try:
        file = open('pos.txt', 'r')
    except OSError:
        print('cannot open ' +  file)
    else:
        pos = int(file.read())
#         print(file, 'has', len(pos.readlines()), 'lines')
        file.close()
#    OG code  # getting previous time stamp
#     file = open("pos.txt","r")
#     pos = int(file.read())
#     file.close()

    # writing next time stamp
    file = open("pos.txt","w")
    file.write(str(pos+interval))
    file.close()

    #returning captions
    return {'caption':printWAV(FILE_NAME, pos=pos, clip=interval)}

def update_captions():
    with app.app_context():
        while True:
            # timing thread waiting for the interval
            time.sleep(interval)

            # forcefully updating captionsPane with caption
            turbo.push(turbo.replace(render_template('captionsPane.html'), 'load'))
            
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")