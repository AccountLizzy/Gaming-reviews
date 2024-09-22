from flask import Flask, render_template, request, redirect, url_for, flash, abort
import message
from database import session, Blogs, User, Comments
import wtforms
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField, CKEditor
from flask_bootstrap import Bootstrap5
import datetime
import bleach
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from functools import wraps
from hashlib import md5


app = Flask(__name__, static_folder='static')

ALLOWED_TAGS = ['p', 'h2', 'strong', 'a', 'ul', 'li', 'strike', 's', 'em', 'i']

# csrf protection
app.config['SECRET_KEY'] = 'HellO!!'

# initialize
bootstrap = Bootstrap5(app)
login_manager = LoginManager()
login_manager.init_app(app)
ckeditor = CKEditor(app)

def avatar(email):
    digest = md5(email.lower().encode('utf-8')).hexdigest()
    return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={100}'

class custom_func():
    def update_response():  # Gets all rows of database
        return session.query(Blogs).all()
    
    def date_now():  # Formats the current time as (month date, year): August 12, 2023
        date = datetime.datetime.now()
        return date.strftime("%B %d, %Y")
    
    def comment_date():  # Formats the current time as yyyy/mm/dd: 2023/08/12
        date = datetime.datetime.now()
        return date.strftime("%Y/%d/%m")
    
    def get_blog_byID(id):  # Get Blogs row by ID
        return session.query(Blogs).filter_by(id=id).first()
    
    def get_img(place):
        placeholder = './static/assets/img/'
        ender = '-bg.jpg'
        return placeholder + place + ender  # eg: about_img = placeholder + 'about' + ender
    
    def get_comments_byID(id):  # Get the specific comments for the blog id
        return session.query(Comments).filter_by(blog_id=id).all()
    
def admin_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1: return abort(403)
        else: return func(*args, **kwargs) # This executes the wrapped function if the user passes the check.
    return wrapper
    


@login_manager.user_loader
def load_user(user_id):
    return session.query(User).filter_by(id=user_id).first()


@app.route('/')
def index():
    posts = custom_func.update_response()
    return render_template('index.html', title="Lizzy's Blogs", img=custom_func.get_img('home_yes'), posts=posts, current_user=current_user, logged_in=current_user.is_authenticated)

@app.route('/about')
def about():
    return render_template('about.html', title='About Me', img=custom_func.get_img('about'))


@app.route('/contact', methods=['GET', 'POST'])
async def contact():
    if request.method == 'GET':
        return render_template('contact.html', title='Contact Me', img=custom_func.get_img('contact'))
    else:
        receiver_email = request.form['email']
        name = request.form['name']
        text = f"{name}\n\n{request.form['text']}\n\n{request.form['phone']}"
        message.send_text(receiver=receiver_email, message=text)
        return render_template('contact.html', title='Message Successfully Sent!', img=custom_func.get_img('contact'))


class CommentForm(FlaskForm):
    comment = CKEditorField("Comments", validators=[DataRequired()])
    submit = SubmitField("Post comment")


@app.route('/<int:index>', methods=['GET', 'POST'])
def show_post(index):
    current_post = custom_func.get_blog_byID(id=index)
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comments(
                text=form.comment.data,
                author=current_user,
                blog_id=index,
            )
            session.add(new_comment)
            session.commit()
            print('Comment added')
        else:
            flash('Please login before commenting.', 'unauthorized commenting')
            print('redirecting to login page')
            return redirect(url_for('login'))
    # CHANGE IMG
    print(current_post)
    return render_template('post.html', title=current_post.title, img=custom_func.get_img('home'), c_post=current_post, form=form, logged_in=current_user.is_authenticated, 
                           comments=custom_func.get_comments_byID(index), date=custom_func.comment_date(), avatar=avatar)


class CreatePost(FlaskForm):
    title = StringField("Blogs Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    image = StringField("Blogs Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blogs Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


@app.route('/create', methods=['GET', 'POST'])
@login_required
@admin_only
def create_post():
    form = CreatePost()
    if form.validate_on_submit():
        new_post = Blogs(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            image=form.image.data,
            author=current_user,
            date=custom_func.date_now()
        )
        session.add(new_post)
        session.commit()
        return redirect(url_for('index'))
    return render_template('make_post.html', title='Create Post', img=custom_func.get_img('home'), form=form)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_only
def edit_post(id):
    Blogs = custom_func.get_blog_byID(id=id)
    if not Blogs:
        print(f"Blogs with id {id} not found.")
        return redirect(url_for('index'))

    form = CreatePost(
        title = Blogs.title,
        subtitle = Blogs.subtitle,
        author = Blogs.author,
        image = Blogs.image,
        date = Blogs.date,
        body = Blogs.body,
    )


    if form.validate_on_submit():
        # Update Blogs attributes
        Blogs.title = request.form.get('title')
        Blogs.subtitle = request.form.get('subtitle')
        Blogs.author = request.form.get('author')
        Blogs.image = request.form.get('image')
        Blogs.body = bleach.clean(request.form.get('body'), tags=ALLOWED_TAGS, strip=True)
        session.commit()
        return redirect(url_for('show_post', index=Blogs.id))

    return render_template('make_post.html', title='Edit Post', img=Blogs.image, form=form)
    

@app.route('/delete/<int:id>')
@login_required
@admin_only
def delete_post(id):
    Blogs = custom_func.get_blog_byID(id=id)
    session.delete(Blogs)
    session.commit()
    return redirect(url_for('index'))


class AddUser(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    name = StringField('Name')
    submit = SubmitField('Sign me up!')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = AddUser()
    if form.validate_on_submit():
        new_user = User(
            email = form.email.data,
            password = generate_password_hash(form.password.data, method='pbkdf2', salt_length=16),
            name = form.name.data
        )
        if new_user:
            try:
                session.add(new_user)
                session.commit()
            except IntegrityError: # For if user already exists and has posed an error
                flash('You already have an account. Please login instead.', 'already registered')

            flash('Welcome back!', 'login')
            return redirect(url_for('login'))
    
    return render_template('register.html', form=form, title='Register', img=custom_func.get_img('register'))



class LoginUser(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign me up!')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginUser()
    if form.validate_on_submit():
        user = session.query(User).filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                print('Logged in!')
                login_user(user=user)
                return redirect(url_for('index'))
            else:
                flash('Incorrect password. Please try again.', 'danger')
                return redirect(url_for('login'))
        else:
            flash('User is nonexistant. Please try again or register instead.', 'null')
            return redirect(url_for('login'))
    return render_template('login.html', title='Login', form=form, img=custom_func.get_img('login'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)