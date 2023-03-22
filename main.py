from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
# a database can contain many tables
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# there are many routes which can only be accessed by admin , so it will be easier to create @admin_only decorator
# first look how @login_required decorator is made , then do similarly , revise decorators on day 54
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise if id=1, continue with the route function
        return f(*args, **kwargs)
    return decorated_function


##CONFIGURE TABLES
class Users(UserMixin, db.Model):  # yo ni blog.db mai hunxa
    # Usermixin ley ithink, Users wala table ho vanera janauxa hola , current_user ma eska ni properties hunivaye
    __tablename__ = "users"  # kei navaneva ni  tablename would be users
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")  # [link with blogposts table[onetomany]]
    # user_object.posts ley tyo user ka posts dinivao, posts will contain blogposts objects
    # *******Add parent relationship*******#
    # "comment_author" refers to the comment_author property/field in the Comment class.
    comments = relationship("Comment", back_populates="comment_author")  # [link with comments [onetomany]]
    # comments will contain Comment objects
# Create all the tables in the database
db.create_all()


class BlogPost(db.Model):  # table containg blogposts
    # back_populates helps to link two fields from different tables
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "posts" refers to the posts protperty in the User class.
    author = relationship("Users", back_populates="posts")
    # author will be a object of Users
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    #***************Parent Relationship*************#
    comments = relationship("Comment", back_populates="parent_post")  # [link blogpost and its associated comments]
db.create_all()


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    # *******Add child relationship*******#
    # "users.id" The users refers to the tablename of the Users class.
    # "comments" refers to the comments property in the User class.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # comment garni author
    # foreign key is the field in one table which is primary key in another table
    # users tablema users ta dherai xan, esle comment garni user chinxa paila by comment_author ani balla tesko id linxa
    comment_author = relationship("Users", back_populates="comments")
    # commenauthor will be a Users object
    #***************Child Relationship*************#
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))  # kun postma comment garya vannikura
    # blosposts table ma ta dherai post xan, comment gareko wala post fetch by parent_post and then tesko id linxa
    parent_post = relationship("BlogPost", back_populates="comments")  # [link comments associated to a post]

db.create_all()


@login_manager.user_loader
def load_user(user_id):   # yo user_id wala user load hunivayo
    return Users.query.get(int(user_id))


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # post method ho vani / submit click garisako vani
        if Users.query.filter_by(email=form.email.data).first():  # email is one of the coulmns
            # User already exists , register garda yo email wala user pailai dekhi exist garepaar databasema
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        new_user = Users(
            username=form.name.data,
            email=form.email.data,
            password=generate_password_hash(password=form.password.data, method="pbkdf2:sha256", salt_length=8)
        )
        db.session.add(new_user)
        db.session.commit()
        # Log in and authenticate user after adding details to database.
        # register garda bitikai ni ta login saraha honita, so register complete garesini login garaidini
        login_user(new_user)
        # return redirect(url_for(get_all_posts))  get_all_posts must be under ""
        return redirect(url_for("get_all_posts"))

    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()

        if not user:  # if user not in database , yo email wala user dont exist , if user: means # if user existss
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))

        # Password incorrect , user exist but password incorrect
        elif not check_password_hash(user.password, form.password.data):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))

        # Email exists and password correct
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
        # or sidai if user and check_password_hash(): login_user(user)  return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    all_comments = requested_post.comments
    if form.validate_on_submit():
        if current_user.is_authenticated:
            cmt = form.comment_text.data
            new_comment = Comment(text=cmt,
                                  comment_author=current_user,
                                  parent_post=requested_post)
            db.session.add(new_comment)
            db.session.commit()
        else:
            # login navako user le cmt garepar: esto error flash gardini
            flash('You need to login or register to comment.`')
            return redirect(url_for('login'))

    return render_template("post.html", post=requested_post, current_user=current_user, form=form, all_comments=all_comments)
    # login vako user = currentuser

@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)

@admin_only
@app.route("/new-post", methods=["GET", "POST"])
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        # current_user only has is_authenticated,get_id(),is_anynomous [login nagareko user hola],is_active
        # current_user.name dont exist esto attribute [galat] current_user.username , etc, Users class kaa sab attribute
        # ni hudaraixan current_user sita
        # current_user_id = current_user.get_id()
        # user = Users.query.get(current_user_id)
        # current_user_name = str(user.username)
        # author must be a Users object coz relationship() lagaxam
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,  # kun userle post haleko vanera
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>")
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    # prepopulate garauna editpost click gardabitikai formlai
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, current_user=current_user)

@admin_only  # admin only can delete , blogpost author can only delete vannakhojya
# html ma delete btn lukaye pani aru userslai, esari manually yo route ni access garna napaun vanera
@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
