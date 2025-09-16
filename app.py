import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
# import openai  # Uncomment if integrating real AI story generation

app = Flask(__name__)  # Create Flask app BEFORE routes
app.secret_key = 'your-secret-key'  # Change in production

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# In-memory "database"
artisans = []
users = []
products = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Serve uploaded files correctly
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- AI Story Placeholder (swap with real AI if desired) ---
def generate_story(product_name):
    return f"This unique creation, '{product_name}', is a symbol of Indian heritage and skill!"

# --- Home Page ---
@app.route('/')
def home():
    return render_template('index.html')

# --- Artisan Signup ---
@app.route('/artisan_signup', methods=['GET', 'POST'])
def artisan_signup():
    if request.method == 'POST':
        data = request.form
        file = request.files['profile_pic']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        artisan = {
            "name": data['name'],
            "phone": data['phone'],
            "email": data['email'],
            "address": data['address'],
            "skills": data['skills'],
            "profile_pic": filename,
            "bank_info": data.get('bank_info', '')
        }
        artisans.append(artisan)
        session['artisan'] = artisan['email']
        return redirect(url_for('upload_product'))
    return render_template('artisan_signup.html')

# --- Product Upload (by Artisan) ---
@app.route('/upload_product', methods=['GET', 'POST'])
def upload_product():
    if 'artisan' not in session:
        return redirect(url_for('artisan_signup'))
    if request.method == 'POST':
        data = request.form
        file = request.files['product_img']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        story = generate_story(data['product_name'])
        customization = {
            "color": data.get('color_options', ''),
            "material": data.get('material_options', ''),
            "design": data.get('design_options', ''),
        }
        product = {
            "name": data['product_name'],
            "price": data['price'],
            "artisan_email": session['artisan'],
            "product_img": filename,
            "story": story,
            "customization": customization
        }
        products.append(product)
        return redirect(url_for('product_list'))
    return render_template('upload_product.html')

# --- User Signup/Login ---
@app.route('/user_signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        data = request.form
        file = request.files['profile_pic']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        user = {
            "name": data['name'],
            "email": data['email'],
            "password": data['password'],
            "profile_pic": filename
        }
        users.append(user)
        session['user'] = user['email']
        return redirect(url_for('product_list'))
    return render_template('user_signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        for user in users:
            if user['email'] == email and user['password'] == password:
                session['user'] = email
                return redirect(url_for('product_list'))
        flash('Invalid credentials')
    return render_template('login.html')

# --- Product List ---
@app.route('/products')
def product_list():
    return render_template('product_list.html', products=products)

# --- Product Details / Customization ---
@app.route('/product/<int:idx>', methods=['GET', 'POST'])
def product_detail(idx):
    product = products[idx]
    if request.method == 'POST':
        # Handle customization and payment here later
        flash('Order placed! Payment flow to be implemented.')
        return redirect(url_for('product_list'))
    return render_template('product_detail.html', product=product, idx=idx)

# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
