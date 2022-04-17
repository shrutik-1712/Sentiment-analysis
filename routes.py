import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from sentiment_analysis import app, db, bcrypt
from sentiment_analysis.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from sentiment_analysis.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
'''from flask_bootstrap import Bootstrap 
# NLP Packages
'''
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob,Word 
import random 
import time

@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)

@app.route('/analysis')
def analysis():
	return render_template('analysis.html')


@app.route('/analyse',methods=['POST'])
def analyse():
    start = time.time()
    if request.method == 'POST':
        rawtext = request.form['rawtext']
        received_text1=rawtext
        blob=rawtext
        sid_obj = SentimentIntensityAnalyzer()
        sentiment_dict = sid_obj.polarity_scores(rawtext)
        neg=sentiment_dict['neg']*100
        neu=sentiment_dict['neu']*100
        pos=sentiment_dict['pos']*100
        '''neu=neu1.round(a_float, 2)
        pos=pos1.round(a_float, 2)
        neu=neu1.round(a_float, 2)'''
        #number_of_tokens = len(list(blob.Words))
        end = time.time()
        final_time = end-start
        return render_template('analysis.html',received_text = received_text1,neg=neg,pos=pos,neu=neu,final_time=final_time)
		#NLP Stuff
#		blob = TextBlob(rawtext)
#		received_text2 = blob
#		blob_sentiment,blob_subjectivity = blob.sentiment.polarity ,blob.sentiment.subjectivity
#		number_of_tokens = len(list(blob.words))
##		# Extracting Main Points
#		nouns = list()
#		for word, tag in blob.tags:
#		    if tag == 'NN':
#		        nouns.append(word.lemmatize())
#		        len_of_words = len(nouns)
#		        rand_words = random.sample(nouns,len(nouns))
#		        final_word = list()
#		        for item in rand_words:
#		        	word = Word(item).pluralize()
#		        	final_word.append(word)
#		        	summary = final_word
#		        	end = time.time()
#		        	final_time = end-start'''


	#return render_template('analysis.html',received_text = received_text2,number_of_tokens=number_of_tokens,blob_sentiment=blob_sentiment,blob_subjectivity=blob_subjectivity,summary=summary,final_time=final_time)
#    return render_template('analysis.html',received_text = receivedtext,number_of_tokens=number_of_tokens,neg=neg,pos=pos,neu=neu,final_time=final_time)
@app.route('/analysis_excel')
def analysis_excel():
     # Set The upload HTML template '\templates\index.html'
    return render_template('analysis_excel.html')
@app.route("/analysis_excel", methods=['GET','POST'])
def uploadFiles():
      # get the uploaded file
      uploaded_file = request.files['filename']
      if uploaded_file.filename != '':
           file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
          # set the file path
           uploaded_file.save(file_path)
          # save the file
      return redirect(url_for('analysis_excel.html'))