import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_pymongo import PyMongo
import google.generativeai as genai

load_dotenv()
db_user = os.getenv("db_user")
db_pass = os.getenv("db_pass")
gemini_api = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change in production

app.config['MONGO_URI'] = f"mongodb+srv://{db_user}:{db_pass}@artisans.s8y9gfm.mongodb.net/marketplace?retryWrites=true&w=majority"
mongo = PyMongo(app)
db = mongo.db

UPLOAD_FOLDER = 'uploads'
ALLOWED_IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_3D_EXTENSIONS = {'glb', 'gltf', 'obj', 'stl'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

artisans = db["artisans"]
users = db["users"]
products = db["product_details"]

def allowed_file(filename, allowed_ext):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        return mongo.send_file(filename)
    except Exception as e:
        return f"File not found: {e}", 404

def generate_story(product_name):
    genai.configure(api_key=gemini_api)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
        f"Share some historical background about {product_name} such that the reader feels like they should buy one."
    )
    return response.text

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/artisan_signup', methods=['GET', 'POST'])
def artisan_signup():
    if request.method == 'POST':
        data = request.form
        file = request.files['profile_pic']
        filename = secure_filename(file.filename)
        mongo.save_file(filename, file)
        artisan = {
            "name": data['name'],
            "phone": data['phone'],
            "email": data['email'],
            "address": data['address'],
            "skills": data['skills'],
            "profile_pic": filename,
            "bank_info": data.get('bank_info', '')
        }
        artisans.insert_one(artisan)
        session['artisan'] = artisan['email']
        return redirect(url_for('upload_product'))
    return render_template('artisan_signup.html')

@app.route('/upload_product', methods=['GET', 'POST'])
def upload_product():
    if 'artisan' not in session:
        return redirect(url_for('artisan_signup'))
    if request.method == 'POST':
        data = request.form
        img_file = request.files['product_img']
        model_file = request.files['product_3dfile']
        img_filename = secure_filename(img_file.filename)
        model_filename = secure_filename(model_file.filename)
        mongo.save_file(img_filename, img_file)
        mongo.save_file(model_filename, model_file)
        story = generate_story(data['product_name'])
        customization = {
            "color": data.get('color_options', ''),
            "material": data.get('material_options', ''),
            "design": data.get('design_options', '')
        }
        product = {
            "name": data['product_name'],
            "price": data['price'],
            "artisan_email": session['artisan'],
            "product_img": img_filename,
            "product_3dfile": model_filename,
            "story": story,
            "customization": customization
        }
        products.insert_one(product)
        return redirect(url_for('product_list'))
    return render_template('upload_product.html')

@app.route('/products')
def product_list():
    return render_template('product_list.html', products=list(products.find()))

@app.route('/product/<int:idx>', methods=['GET', 'POST'])
def product_detail(idx):
    products_list = list(products.find())
    if idx <= 0 or idx > len(products_list):
        flash('Product does not exist!')
        return redirect(url_for('product_list'))
    product = products_list[idx - 1]
    if request.method == 'POST':
        flash('Order placed! Payment flow to be implemented.')
        return redirect(url_for('product_list'))
    return render_template('product_detail.html', product=product, idx=idx)

@app.route('/user_signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        data = request.form
        file = request.files['profile_pic']
        filename = secure_filename(file.filename)
        mongo.save_file(filename, file)
        user = {
            "name": data['name'],
            "email": data['email'],
            "password": data['password'],
            "profile_pic": filename
        }
        users.insert_one(user)
        session['user'] = user['email']
        return redirect(url_for('product_list'))
    return render_template('user_signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users.find_one({'email': email, 'password': password})
        if user:
            session['user'] = email
            return redirect(url_for('product_list'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
