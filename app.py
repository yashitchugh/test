import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from bson.objectid import ObjectId


load_dotenv()
db_user = os.getenv("db_user")
db_pass = os.getenv("db_pass")
hf_api = os.getenv("HUGGINGFACEHUB_API_TOKEN")
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change in production

UPLOAD_FOLDER = 'uploads'
ALLOWED_IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_3D_EXTENSIONS = {'glb', 'gltf', 'obj', 'stl'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

artisans = []
users = []
products = []


def allowed_file(filename, allowed_ext):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext


# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        # Retrieve the file from GridFS
        return mongo.send_file(filename)
    except Exception as e:
        return f"File not found: {e}", 404


os.environ["HUGGINGFACEHUB_API_TOKEN"] = hf_api


def generate_story(product_name):
    client = InferenceClient(api_key=hf_api)
    response = client.chat_completion(
        model="HuggingFaceH4/zephyr-7b-beta",
        messages=[
            {"role": "system", "content": "You are a salesman."},
            {"role": "user", "content": f"Share some historical background about {product_name} such that the reader feels like they should buy one."}
        ],
        max_tokens=200,
        temperature=0.7
    )
    return response.choices[0].message["content"]


@app.route('/')
def home():
    return render_template('index.html')


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
            "profile_pic": file_id,
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
        if not allowed_file(img_filename, ALLOWED_IMG_EXTENSIONS):
            flash('Invalid image type. Allowed: png, jpg, jpeg, gif.')
            return redirect(request.url)
        img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))

        model_filename = secure_filename(model_file.filename)
        if not allowed_file(model_filename, ALLOWED_3D_EXTENSIONS):
            flash('Invalid 3D model type. Allowed: glb, gltf, obj, stl.')
            return redirect(request.url)
        model_file.save(os.path.join(
            app.config['UPLOAD_FOLDER'], model_filename))

        story = generate_story(data['product_name'])

        customization = {
            "color": data.get("color_options", ""),
            "material": data.get("material_options", ""),
            "design": data.get("design_options", "")
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
        products.append(product)
        return redirect(url_for('product_list'))

    return render_template('upload_product.html')

@app.route('/products')
def product_list():
    product_list = list(products.find())
    return render_template('product_list.html', products=product_list)

@app.route('/user_signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        data = request.form
        file = request.files['profile_pic']
        filename = secure_filename(file.filename)
        # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Save file to GridFS and get the unique ID
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
        for user in users:
            if user['email'] == email and user['password'] == password:
                session['user'] = email
                return redirect(url_for('product_list'))
        flash('Invalid credentials')
    return render_template('login.html')


@app.route('/products')
def product_list():
    return render_template('product_list.html', products=products)


@app.route('/product/<int:idx>', methods=['GET', 'POST'])
def product_detail(idx):
    products_len = products.count_documents({})
    if idx <= 0 or idx > products_len:
        flash('Product does not exist!')
        return redirect(url_for('product_list'))
    product = products.find().sort('_id', 1).skip(idx).next()
    if request.method == 'POST':
        # Placeholder for customization/payment
        flash('Order placed! Payment flow to be implemented.')
        return redirect(url_for('product_list'))
    return render_template('product_detail.html', product=product, idx=idx)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)