from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import send_from_directory, abort

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session management and flash messages
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx'}

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Make sure this is correct
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'

mail = Mail(app)

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db = SQLAlchemy(app)

# Serializer for generating tokens
s = URLSafeTimedSerializer(app.secret_key)

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)  # Make sure this line exists

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
# Notes Model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    views = db.Column(db.Integer, default=0)  # Track the number of views
    user = db.relationship('User', backref=db.backref('notes', lazy=True))
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Route to upload notes
@app.route('/upload_note', methods=['GET', 'POST'])
@login_required
def upload_note():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        subject = request.form['subject']
        file = request.files['file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            new_note = Note(title=title, description=description, subject=subject, file_name=filename, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()

            flash('Note uploaded successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid file type. Only PDF and DOCX files are allowed.', 'danger')

    return render_template('upload_note.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if not user.email_verified:
                flash('Please verify your email first.', 'warning')
                return redirect(url_for('login'))

            login_user(user)
            flash('Login Successful!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        if User.query.filter_by(email=email).first():
            flash('Email address already registered!', 'danger')
            return redirect(url_for('signup'))

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        token = s.dumps(email, salt='email-confirm')
        confirm_url = url_for('confirm_email', token=token, _external=True)
        msg = Message('Confirm Your Email', sender='your-email@example.com', recipients=[email])
        msg.body = f'Please click the link to confirm your email: {confirm_url}'
        mail.send(msg)

        flash('Account created! Please check your email to confirm your email address.', 'info')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)  # 1 hour expiration
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('signup'))

    user = User.query.filter_by(email=email).first_or_404()

    if user.email_verified:
        flash('Account already verified. Please login.', 'success')
    else:
        user.email_verified = True
        db.session.commit()
        flash('Your account has been verified! You can now log in.', 'success')

    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            token = s.dumps(email, salt='password-reset')
            reset_url = url_for('reset_token', token=token, _external=True)
            msg = Message('Reset Your Password', sender='your-email@example.com', recipients=[email])
            msg.body = f'Please click the link to reset your password: {reset_url}'
            mail.send(msg)
            flash('Password reset email sent! Please check your inbox.', 'info')
        else:
            flash('Email address not found.', 'danger')

    return render_template('reset_password.html')

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_token(token):
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)  # 1 hour expiration
    except:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('reset_password'))

    if request.method == 'POST':
        user = User.query.filter_by(email=email).first_or_404()
        new_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        user.password = new_password
        db.session.commit()
        flash('Your password has been updated! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_token.html')

@app.route('/users')
def get_users():
    users = User.query.all()  # Fetch all users
    user_data = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
    return {'users': user_data}

# Route to display the home page with popular notes
@app.route('/')
def home():
    notes = Note.query.all()  # Get all notes
    return render_template('index.html', notes=notes)

# Route to view a note (increments the view count)
@app.route('/note/<int:note_id>')
def view_note(note_id):
    note = Note.query.get_or_404(note_id)
    note.views += 1  # Increment the view count
    db.session.commit()
    return render_template('view_note.html', note=note)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        # Normally, you would process the data, e.g., store it in a database or send an email
        # For now, we will just flash a success message.
        
        flash(f'Thank you, {name}! Your message has been received.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/profile')
@login_required
def profile():
    user_notes = Note.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', notes=user_notes)

@app.route('/delete_note/<int:note_id>')
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        flash('You do not have permission to delete this note.', 'danger')
        return redirect(url_for('profile'))

    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    note = Note.query.filter_by(file_name=filename).first_or_404()

    # Increment the view count
    note.views += 1
    db.session.commit()

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/python-notes')
def python_notes():
    return render_template('python_notes.html')

@app.route('/cpp-notes')
def cpp_notes():
    return render_template('cpp_notes.html')

@app.route('/java-notes')
def java_notes():
    return render_template('java_notes.html')

@app.route('/sql-notes')
def sql_notes():
    return render_template('sql_notes.html')

@app.route('/flask-notes')
def flask_notes():
    return render_template('flask_notes.html')

@app.route('/youtube_notes')
def youtube_notes():
    return render_template('youtube_notes.html')

@app.route('/django_notes')
def django_notes():
    return render_template('django_notes.html')

@app.route('/react_notes')
def react_notes():
    return render_template('react_notes.html')

@app.route('/r_notes')
def r_notes():
    return render_template('r_notes.html')

@app.route('/nodejs_notes')
def nodejs_notes():
    return render_template('nodejs_notes.html')

if __name__ == '__main__':
    with app.app_context():
        # Create the database tables if they don't exist
        db.create_all()
    app.run(debug=True)