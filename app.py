from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
# from flask_wtf.csrf import exempt
from wtforms import StringField, PasswordField, TextAreaField, DecimalField, IntegerField, SelectField, FileField
from wtforms.validators import DataRequired, Email, Length, NumberRange
from models.models import db, User, Category, Product, Order, OrderItem, CartItem, Wishlist, ProductView
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from forms.profile_forms import ProfileForm
import os
import uuid
from flask_mail import Mail, Message
import stripe
from decimal import Decimal
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# PostgreSQL Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Handle Heroku postgres URL format
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Local development PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql://{os.environ.get('DB_USER', 'postgres')}:"
        f"{os.environ.get('DB_PASSWORD', 'password')}@"
        f"{os.environ.get('DB_HOST', 'localhost')}:"
        f"{os.environ.get('DB_PORT', '5432')}/"
        f"{os.environ.get('DB_NAME', 'only_db')}"
    )

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# csrf = CSRFProtect(app)

# Mail Configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Stripe Configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
app.config['STRIPE_PUBLISHABLE_KEY'] = os.environ.get('STRIPE_PUBLISHABLE_KEY')

mail = Mail(app)
db.init_app(app)
tax_rate = Decimal("0.08")

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Account Type', choices=[('buyer', 'Buyer'), ('seller', 'Seller')], default='buyer')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0.01)])
    stock_quantity = IntegerField('Stock Quantity', validators=[DataRequired(), NumberRange(min=0)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    image = FileField('Product Image')
    additional_images = FileField('Additional Images')

# ProfileForm is now imported from forms/profile_forms.py

# Password reset is handled directly through request.form, no WTForm needed

# Helper Functions
def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def get_cart_count():
    session_id = get_session_id()
    return CartItem.query.filter_by(session_id=session_id).count()

def get_cart_items():
    session_id = get_session_id()
    return CartItem.query.filter_by(session_id=session_id).all()

# Authentication Routes and Helper Functions
@app.context_processor
def inject_cart_count():
    return dict(get_cart_count=get_cart_count)

@app.context_processor
def inject_current_user():
    def get_current_user():
        if 'user_id' in session:
            return User.query.get(session['user_id'])
        return None
    return dict(get_current_user=get_current_user)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def seller_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if session.get('user_role') != 'seller':
            flash('Access denied. Seller account required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.role
            
            # Transfer guest cart to user if exists
            if 'session_id' in session:
                guest_cart_items = CartItem.query.filter_by(session_id=session['session_id']).all()
                for item in guest_cart_items:
                    # Check if user already has this product in cart
                    existing_item = CartItem.query.filter_by(
                        session_id=f"user_{user.id}",
                        product_id=item.product_id
                    ).first()
                    
                    if existing_item:
                        existing_item.quantity += item.quantity
                    else:
                        item.session_id = f"user_{user.id}"
                    
                    db.session.delete(item) if existing_item else None
                
                db.session.commit()
                session['session_id'] = f"user_{user.id}"
            else:
                session['session_id'] = f"user_{user.id}"
            
            #flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect based on user role
            if user.role == 'seller':
                return redirect(url_for('seller_dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter(
            (User.email == form.email.data) | (User.username == form.username.data)
        ).first()
        
        if existing_user:
            flash('Username or email already exists.', 'error')
        else:
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                role=form.role.data
            )
            db.session.add(user)
            db.session.commit()
            
            # Log in the new user
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.role
            
            # Transfer guest cart to user if exists
            if 'session_id' in session:
                guest_cart_items = CartItem.query.filter_by(session_id=session['session_id']).all()
                for item in guest_cart_items:
                    item.session_id = f"user_{user.id}"
                db.session.commit()
                session['session_id'] = f"user_{user.id}"
            else:
                session['session_id'] = f"user_{user.id}"
            
            flash(f'Welcome to Only, {user.username}!', 'success')
            
            # Redirect based on user role
            if user.role == 'seller':
                return redirect(url_for('seller_dashboard'))
            else:
                return redirect(url_for('home'))
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
def logout():
    username = session.get('username', 'User')
    session.clear()
    #flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('home'))

# Profile Routes
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    form = ProfileForm()
    
    if form.validate_on_submit():
        # Check if username or email already exists (excluding current user)
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data),
            User.id != user.id
        ).first()
        
        if existing_user:
            flash('Username or email already exists.', 'error')
        else:
            # Update user information
            user.username = form.username.data
            user.email = form.email.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            
            # Update structured phone fields
            user.phone_country_code = form.phone_country_code.data
            user.phone_number = form.phone_number.data
            # Keep legacy fields for backward compatibility
            if form.phone_country_code.data and form.phone_number.data:
                user.phone = f"{form.phone_country_code.data}{form.phone_number.data}"
            else:
                user.phone = form.phone.data
            
            # Update structured address fields
            user.address_line1 = form.address_line1.data
            user.address_line2 = form.address_line2.data
            user.city = form.city.data
            user.state_province = form.state_province.data
            user.postal_code = form.postal_code.data
            user.country = form.country.data
            # Keep legacy field for backward compatibility
            if form.address_line1.data or form.city.data or form.country.data:
                address_parts = []
                if form.address_line1.data:
                    address_parts.append(form.address_line1.data)
                if form.address_line2.data:
                    address_parts.append(form.address_line2.data)
                if form.city.data:
                    address_parts.append(form.city.data)
                if form.state_province.data:
                    address_parts.append(form.state_province.data)
                if form.postal_code.data:
                    address_parts.append(form.postal_code.data)
                if form.country.data:
                    address_parts.append(form.country.data)
                user.address = ", ".join(address_parts)
            else:
                user.address = form.address.data
            
            # Handle avatar upload
            if form.avatar.data:
                filename = secure_filename(form.avatar.data.filename)
                if filename:
                    filename = f"avatar_{user.id}_{uuid.uuid4()}_{filename}"
                    form.avatar.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    user.avatar_url = f"/static/uploads/{filename}"
            
            # Update company information for sellers
            if user.role == 'seller':
                user.company_name = form.company_name.data
                user.company_description = form.company_description.data
                user.company_website = form.company_website.data
                
                # Update structured company phone fields
                user.company_phone_country_code = form.company_phone_country_code.data
                user.company_phone_number = form.company_phone_number.data
                # Keep legacy field for backward compatibility
                if form.company_phone_country_code.data and form.company_phone_number.data:
                    user.company_phone = f"{form.company_phone_country_code.data}{form.company_phone_number.data}"
                else:
                    user.company_phone = form.company_phone.data
                
                # Update structured company address fields
                user.company_address_line1 = form.company_address_line1.data
                user.company_address_line2 = form.company_address_line2.data
                user.company_city = form.company_city.data
                user.company_state_province = form.company_state_province.data
                user.company_postal_code = form.company_postal_code.data
                user.company_country = form.company_country.data
                # Keep legacy field for backward compatibility
                if form.company_address_line1.data or form.company_city.data or form.company_country.data:
                    address_parts = []
                    if form.company_address_line1.data:
                        address_parts.append(form.company_address_line1.data)
                    if form.company_address_line2.data:
                        address_parts.append(form.company_address_line2.data)
                    if form.company_city.data:
                        address_parts.append(form.company_city.data)
                    if form.company_state_province.data:
                        address_parts.append(form.company_state_province.data)
                    if form.company_postal_code.data:
                        address_parts.append(form.company_postal_code.data)
                    if form.company_country.data:
                        address_parts.append(form.company_country.data)
                    user.company_address = ", ".join(address_parts)
                else:
                    user.company_address = form.company_address.data
                
                # Handle company logo upload
                if form.company_logo.data:
                    filename = secure_filename(form.company_logo.data.filename)
                    if filename:
                        filename = f"logo_{user.id}_{uuid.uuid4()}_{filename}"
                        form.company_logo.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        user.company_logo_url = f"/static/uploads/{filename}"
            
            db.session.commit()
            
            # Update session username if changed
            session['username'] = user.username
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
    
    # Pre-populate form with existing data
    if request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
        form.phone.data = user.phone
        form.address.data = user.address
        
        if user.role == 'seller':
            form.company_name.data = user.company_name
            form.company_description.data = user.company_description
            form.company_website.data = user.company_website
            form.company_phone.data = user.company_phone
            form.company_address.data = user.company_address
    
    return render_template('profile.html', form=form, user=user)

@app.route('/reset-password', methods=['POST'])
@login_required
def reset_password():
    import secrets
    import string
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('profile'))
        
        # Get form data directly from request
        current_password = request.form.get('current_password', '').strip()
        confirm_reset = request.form.get('confirm_reset', '').strip()
        
        print(f"Debug - Current password provided: {'Yes' if current_password else 'No'}")
        print(f"Debug - Confirm reset provided: {confirm_reset}")
        print(f"Debug - User ID: {user.id}")
        
        # Validate inputs
        if not current_password:
            flash('Current password is required.', 'error')
            return redirect(url_for('profile'))
        
        if not confirm_reset:
            flash('Please type "RESET" to confirm password reset.', 'error')
            return redirect(url_for('profile'))
        
        # Verify current password using check_password_hash
        password_valid = check_password_hash(user.password_hash, current_password)
        print(f"Debug - Password valid: {password_valid}")
        
        if not password_valid:
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('profile'))
        
        # Verify confirmation
        if confirm_reset.upper() != 'RESET':
            flash('Please type "RESET" exactly to confirm password reset.', 'error')
            return redirect(url_for('profile'))
        
        # Generate random 12-character password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        new_password = ''.join(secrets.choice(alphabet) for i in range(12))
        
        print(f"Debug - New password generated: {new_password}")
        
        # Update password with proper hashing
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        print("Debug - Password updated successfully")
        
        flash(f'Password reset successfully! Your new password is: <strong>{new_password}</strong><br><small class="text-muted">Please save this password in a secure location.</small>', 'success')
        return redirect(url_for('profile'))
        
    except Exception as e:
        print(f"Debug - Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Password reset failed: {str(e)}', 'error')
        return redirect(url_for('profile'))

# Main Routes
@app.route('/')
def home():
    # Get featured products (latest 8 products)
    featured_products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
    categories = Category.query.all()
    return render_template('home.html', featured_products=featured_products, categories=categories)

from decimal import Decimal # Ensure this import is present at the top of the file

@app.route('/shop')
def shop():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'newest')  # Default sort is 'newest'
    
    # 1. Price Filtering Parameters
    min_price_str = request.args.get('min_price')
    max_price_str = request.args.get('max_price')
    
    min_price = None
    max_price = None
    
    try:
        # Convert price strings to Decimal for accurate database queries
        if min_price_str:
            min_price = Decimal(min_price_str)
        if max_price_str:
            max_price = Decimal(max_price_str)
    except:
        # Log or ignore bad input, setting to None effectively disables filter
        pass 

    query = Product.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        # Use ilike for case-insensitive search in PostgreSQL
        query = query.filter(Product.name.ilike(f'%{search}%'))
        
    # ✅ Apply Price Range Filters
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
        
    # ✅ Sorting Logic (now matches template values)
    if sort_by == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'name':
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.created_at.desc())

    # Responsive pagination based on screen size
    # Default to 9 items per page for better mobile experience
    per_page = 9
    
    products = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get user's wishlist items if logged in
    user_wishlist = []
    if 'user_id' in session:
        user_wishlist = [
            item.product_id for item in 
            Wishlist.query.filter_by(user_id=session['user_id']).all()
        ]
    
    categories = Category.query.all()
    return render_template('shop.html', 
                          products=products, 
                          categories=categories, 
                          current_category=category_id, 
                          search=search,
                          min_price=min_price_str,  # Pass original strings back to template
                          max_price=max_price_str,
                          sort_by=sort_by,          # Pass sort option back to template
                          user_wishlist=user_wishlist)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id
    ).limit(4).all()
    
    # Track the full detail view (only for buyers, not sellers of their own products)
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        # Only track if user is a buyer or if seller is viewing someone else's product
        if user.role == 'buyer' or (user.role == 'seller' and product.seller_id != user.id):
            track_product_view(product_id, 'full_detail')
    else:
        # Track for guest users
        track_product_view(product_id, 'full_detail')
    
    # Check if product is in user's wishlist
    is_in_wishlist = False
    if 'user_id' in session:
        wishlist_item = Wishlist.query.filter_by(
            user_id=session['user_id'],
            product_id=product_id
        ).first()
        is_in_wishlist = wishlist_item is not None
    
    # Check if current user is the seller (to prevent buying own products)
    is_own_product = False
    if 'user_id' in session:
        is_own_product = product.seller_id == session['user_id']
    
    return render_template('product_detail.html', 
                          product=product, 
                          related_products=related_products,
                          is_in_wishlist=is_in_wishlist,
                          is_own_product=is_own_product)

# Cart Routes

@app.route("/cart")
def cart():
    session_id = get_session_id()
    cart_items = CartItem.query.filter_by(session_id=session_id).all()
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    tax_rate = Decimal("0.08")
    shipping_threshold = Decimal("50.00")
    shipping_cost = Decimal("5.99")
    
    tax = total * tax_rate
    shipping = Decimal("0.00") if total >= shipping_threshold else shipping_cost
    grand_total = total + tax + shipping
    remaining_for_free_shipping = (
        shipping_threshold - total if total < shipping_threshold else Decimal("0.00")
    )

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total,
        tax=tax,
        shipping=shipping,
        grand_total=grand_total,
        remaining_for_free_shipping=remaining_for_free_shipping
    )

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
# @csrf.exempt
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Prevent sellers from buying their own products
    if 'user_id' in session and product.seller_id == session['user_id']:
        flash('You cannot buy your own products!', 'error')
        return redirect(request.referrer or url_for('shop'))
    
    quantity = int(request.form.get('quantity', 1))
    session_id = get_session_id()
    
    # Check if item already in cart
    cart_item = CartItem.query.filter_by(
        session_id=session_id,
        product_id=product_id
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            session_id=session_id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    flash(f'{product.name} added to cart!', 'success')
    
    return redirect(request.referrer or url_for('shop'))

@app.route('/update-cart/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
    else:
        db.session.delete(cart_item)
    
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/remove-from-cart/<int:item_id>')
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))

# API Routes for AJAX
@app.route('/api/cart-items')
def api_cart_items():
    session_id = get_session_id()
    cart_items = CartItem.query.filter_by(session_id=session_id).all()
    
    items = []
    total = 0
    for item in cart_items:
        item_total = float(item.product.price) * item.quantity
        total += item_total
        items.append({
            'id': item.id,
            'name': item.product.name,
            'price': float(item.product.price),
            'quantity': item.quantity,
            'total': item_total,
            'image_url': item.product.image_url,
            'stock_quantity': item.product.stock_quantity
        })
    
    return jsonify({
        'items': items,
        'total': total,
        'count': len(items),
        'shipping': 0 if total >= 50 else 5.99,
        'tax': total * 0.08
    })

@app.route('/api/cart-count')
def api_cart_count():
    return jsonify({'count': get_cart_count()})

@app.route('/api/add-to-cart/<int:product_id>', methods=['POST'])
# @csrf.exempt
def api_add_to_cart(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        
        # Prevent sellers from buying their own products
        if 'user_id' in session and product.seller_id == session['user_id']:
            return jsonify({
                'success': False,
                'message': 'You cannot buy your own products!'
            }), 400
        
        quantity = int(request.json.get('quantity', 1))
        session_id = get_session_id()
        
        # Check stock availability
        if product.stock_quantity < quantity:
            return jsonify({
                'success': False,
                'message': 'Not enough stock available'
            }), 400
        
        # Check if item already in cart
        cart_item = CartItem.query.filter_by(
            session_id=session_id,
            product_id=product_id
        ).first()
        
        if cart_item:
            new_quantity = cart_item.quantity + quantity
            if product.stock_quantity < new_quantity:
                return jsonify({
                    'success': False,
                    'message': 'Not enough stock available'
                }), 400
            cart_item.quantity = new_quantity
        else:
            cart_item = CartItem(
                session_id=session_id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(cart_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{product.name} added to cart!',
            'cart_count': get_cart_count()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'An error occurred while adding to cart'
        }), 500

@app.route('/api/update-cart-item/<int:item_id>', methods=['POST'])
def api_update_cart_item(item_id):
    try:
        cart_item = CartItem.query.get_or_404(item_id)
        quantity = int(request.json.get('quantity', 1))
        
        if quantity <= 0:
            db.session.delete(cart_item)
        else:
            if cart_item.product.stock_quantity < quantity:
                return jsonify({
                    'success': False,
                    'message': 'Not enough stock available'
                }), 400
            cart_item.quantity = quantity
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'cart_count': get_cart_count()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating cart'
        }), 500

@app.route('/api/remove-cart-item/<int:item_id>', methods=['DELETE'])
def api_remove_cart_item(item_id):
    try:
        cart_item = CartItem.query.get_or_404(item_id)
        db.session.delete(cart_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item removed from cart',
            'cart_count': get_cart_count()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'An error occurred while removing item'
        }), 500

@app.route('/api/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    try:
        user_id = session['user_id']
        product = Product.query.get_or_404(product_id)
        
        # Prevent sellers from adding their own products to wishlist
        if product.seller_id == user_id:
            return jsonify({
                'success': False,
                'message': 'You cannot add your own products to wishlist!'
            }), 400
        
        # Check if already in wishlist
        existing_wishlist = Wishlist.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()
        
        if existing_wishlist:
            return jsonify({
                'success': False,
                'message': 'Product already in wishlist!'
            }), 400
        
        # Add to wishlist
        wishlist_item = Wishlist(
            user_id=user_id,
            product_id=product_id
        )
        db.session.add(wishlist_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Added to wishlist!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to add to wishlist'
        }), 500

@app.route('/api/wishlist/remove/<int:product_id>', methods=['DELETE'])
@login_required
def remove_from_wishlist(product_id):
    try:
        user_id = session['user_id']
        
        wishlist_item = Wishlist.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first_or_404()
        
        db.session.delete(wishlist_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Removed from wishlist!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to remove from wishlist'
        }), 500

@app.route('/api/product/<int:product_id>/quick-view')
def product_quick_view(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Track the quick view (only for buyers, not sellers of their own products)
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        # Only track if user is a buyer or if seller is viewing someone else's product
        if user.role == 'buyer' or (user.role == 'seller' and product.seller_id != user.id):
            track_product_view(product_id, 'quick_view')
    else:
        # Track for guest users
        track_product_view(product_id, 'quick_view')
    
    return render_template('partials/quick_view.html', product=product)

@app.route('/api/product/<int:product_id>/track-view', methods=['POST'])
def track_view_api(product_id):
    """API endpoint to track product views"""
    try:
        data = request.get_json()
        view_type = data.get('view_type', 'quick_view')
        
        # Validate view_type
        if view_type not in ['quick_view', 'full_detail']:
            return jsonify({'success': False, 'message': 'Invalid view type'}), 400
        
        product = Product.query.get_or_404(product_id)
        
        # Only track for buyers or sellers viewing other's products
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user.role == 'buyer' or (user.role == 'seller' and product.seller_id != user.id):
                track_product_view(product_id, view_type)
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'message': 'Sellers cannot view their own products for analytics'})
        else:
            # Track for guest users
            track_product_view(product_id, view_type)
            return jsonify({'success': True})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def track_product_view(product_id, view_type):
    """Helper function to track product views"""
    try:
        user_id = session.get('user_id')
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        user_agent = request.headers.get('User-Agent', '')
        
        # Create view record
        view = ProductView(
            user_id=user_id,
            product_id=product_id,
            view_type=view_type,
            ip_address=ip_address,
            user_agent=user_agent[:500]  # Truncate to fit column
        )
        
        db.session.add(view)
        db.session.commit()
        
    except Exception as e:
        print(f"Error tracking view: {e}")
        # Don't fail the main request if view tracking fails
        pass

# Seller Routes
@app.route('/seller/dashboard')
@seller_required
def seller_dashboard():
    from datetime import datetime, timedelta
    from sqlalchemy import func, distinct
    
    user_id = session['user_id']

    # Get seller statistics
    total_products = Product.query.filter_by(seller_id=user_id).count()

    total_orders = (
        db.session.query(Order)
        .join(OrderItem)
        .join(Product)
        .filter(Product.seller_id == user_id)
        .count()
    )

    # Calculate total revenue (sum of order item prices * quantity for this seller)
    total_revenue = (
        db.session.query(db.func.sum(OrderItem.price * OrderItem.quantity))
        .join(Product)
        .filter(Product.seller_id == user_id)
        .scalar()
    ) or 0

    # Calculate daily order performance (today vs yesterday)
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Orders today
    orders_today = (
        db.session.query(Order)
        .join(OrderItem)
        .join(Product)
        .filter(
            Product.seller_id == user_id,
            func.date(Order.created_at) == today
        )
        .count()
    )
    
    # Orders yesterday
    orders_yesterday = (
        db.session.query(Order)
        .join(OrderItem)
        .join(Product)
        .filter(
            Product.seller_id == user_id,
            func.date(Order.created_at) == yesterday
        )
        .count()
    )
    
    # Calculate percentage change
    if orders_yesterday > 0:
        daily_change_percent = ((orders_today - orders_yesterday) / orders_yesterday) * 100
    else:
        daily_change_percent = 100 if orders_today > 0 else 0
    
    daily_change_direction = "increase" if daily_change_percent >= 0 else "decrease"
    daily_change_percent = abs(daily_change_percent)

    # Count new customers (unique customers who bought seller's products)
    new_customers_count = (
        db.session.query(func.count(distinct(Order.user_id)))
        .join(OrderItem)
        .join(Product)
        .filter(Product.seller_id == user_id)
        .scalar()
    ) or 0

    # Calculate average rating based on wishlist counts
    # Get all seller's products with their wishlist counts
    products_wishlist_data = (
        db.session.query(
            Product.id,
            func.count(Wishlist.id).label('wishlist_count')
        )
        .outerjoin(Wishlist, Product.id == Wishlist.product_id)
        .filter(Product.seller_id == user_id)
        .group_by(Product.id)
        .all()
    )
    
    if products_wishlist_data:
        # Calculate average wishlist count as a rating (scale 1-5)
        total_wishlist_count = sum(item.wishlist_count for item in products_wishlist_data)
        product_count = len(products_wishlist_data)
        avg_wishlist_per_product = total_wishlist_count / product_count if product_count > 0 else 0
        
        # Convert to 1-5 scale (assuming 10+ wishlists = 5 stars)
        average_rating = min(5.0, max(1.0, (avg_wishlist_per_product / 2) + 1))
        average_rating = f"{average_rating:.1f}"
    else:
        average_rating = "0.0"

    # Calculate total views for seller's products
    total_views = (
        db.session.query(func.count(ProductView.id))
        .join(Product, ProductView.product_id == Product.id)
        .filter(Product.seller_id == user_id)
        .scalar()
    ) or 0

    # Recent products
    recent_products = (
        Product.query.filter_by(seller_id=user_id)
        .order_by(Product.created_at.desc())
        .limit(5)
        .all()
    )

    # Recent orders for this seller (with proper filtering)
    recent_orders = (
        db.session.query(Order)
        .join(OrderItem)
        .join(Product)
        .filter(Product.seller_id == user_id)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        'seller/dashboard.html',
        total_products=total_products,
        total_orders=total_orders,
        total_revenue=total_revenue,
        recent_products=recent_products,
        recent_orders=recent_orders,
        average_rating=average_rating,
        daily_change_percent=daily_change_percent,
        daily_change_direction=daily_change_direction,
        new_customers_count=new_customers_count,
        orders_today=orders_today,
        total_views=total_views
    )

@app.route('/seller/duplicate-product/<int:product_id>', methods=['POST'])
@seller_required
def duplicate_product(product_id):
    """Duplicates an existing product, setting the name to 'COPY of...'"""
    # 1. Get the original product and ensure seller ownership
    original_product = Product.query.filter_by(
        id=product_id, 
        seller_id=session['user_id']
    ).first_or_404()
    
    # 2. Create a new Product object by copying attributes
    new_product = Product(
        # Create a distinct name
        name=f"COPY of {original_product.name}",
        description=original_product.description,
        price=original_product.price,
        stock_quantity=original_product.stock_quantity,
        category_id=original_product.category_id,
        seller_id=original_product.seller_id, # Inherits the seller ID
        image_url=original_product.image_url,
        additional_images=original_product.additional_images.copy() if original_product.additional_images else None,
        created_at=datetime.utcnow() # Set a new creation date
    )
    
    # 3. Save the new product to the database
    db.session.add(new_product)
    db.session.commit()
    
    flash(f'Product "{original_product.name}" duplicated successfully. You are now editing the copy.', 'success')
    
    # Redirect to the edit page of the new product
    return redirect(url_for('edit_product', product_id=new_product.id))

@app.route('/seller/products')
@seller_required
def seller_products():
    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    
    products = Product.query.filter_by(seller_id=user_id).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('seller/products.html', products=products)

@app.route('/seller/delete-product/<int:product_id>', methods=['POST'])
@seller_required
def delete_product(product_id):
    """Deletes a product and ensures it belongs to the current seller."""
    
    # 1. Get the product and verify ownership
    product = Product.query.filter_by(
        id=product_id, 
        seller_id=session['user_id']
    ).first_or_404()
    
    product_name = product.name
    
    # 2. Delete the product
    db.session.delete(product)
    db.session.commit()
    
    flash(f'Product "{product_name}" deleted successfully.', 'info')
    
    # Redirect back to the seller product list
    return redirect(url_for('seller_products'))

@app.route('/seller/add-product', methods=['GET', 'POST'])
@seller_required
def add_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        # Handle main image upload
        image_url = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            if filename:
                filename = f"{uuid.uuid4()}_{filename}"
                form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = f"/static/uploads/{filename}"
        
        # Handle additional images upload
        additional_images = []
        additional_images_files = request.files.getlist('additional_images')
        for img_file in additional_images_files:
            if img_file and img_file.filename:
                filename = secure_filename(img_file.filename)
                if filename:
                    filename = f"{uuid.uuid4()}_{filename}"
                    img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    additional_images.append(f"/static/uploads/{filename}")
        
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock_quantity=form.stock_quantity.data,
            category_id=form.category_id.data,
            seller_id=session['user_id'],
            image_url=image_url,
            additional_images=additional_images if additional_images else None
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('seller_products'))
    
    return render_template('seller/add_product.html', form=form)

@app.route('/seller/edit-product/<int:product_id>', methods=['GET', 'POST'])
@seller_required
def edit_product(product_id):
    # Get the product and ensure it belongs to the current seller
    product = Product.query.filter_by(id=product_id, seller_id=session['user_id']).first_or_404()
    
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        # Update product fields
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.stock_quantity = form.stock_quantity.data
        product.category_id = form.category_id.data
        
        # Handle main image upload (only if new image is provided)
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            if filename:
                filename = f"{uuid.uuid4()}_{filename}"
                form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.image_url = f"/static/uploads/{filename}"
        
        # Handle additional images
        current_additional_images = product.additional_images or []
        
        # Handle removed images
        removed_images_str = request.form.get('removed_images', '[]')
        try:
            import json
            removed_images = json.loads(removed_images_str) if removed_images_str != '[]' else []
            # Remove deleted images from current list
            current_additional_images = [img for img in current_additional_images if img not in removed_images]
        except:
            pass  # If parsing fails, keep current images
        
        # Handle new additional images upload
        additional_images_files = request.files.getlist('additional_images')
        for img_file in additional_images_files:
            if img_file and img_file.filename:
                filename = secure_filename(img_file.filename)
                if filename:
                    filename = f"{uuid.uuid4()}_{filename}"
                    img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    current_additional_images.append(f"/static/uploads/{filename}")
        
        # Limit to 4 additional images
        product.additional_images = current_additional_images[:4] if current_additional_images else None
        
        db.session.commit()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('seller_products'))
    
    # Pre-populate form with existing product data
    if request.method == 'GET':
        form.name.data = product.name
        form.description.data = product.description
        form.price.data = product.price
        form.stock_quantity.data = product.stock_quantity
        form.category_id.data = product.category_id
    
    return render_template('edit_product.html', form=form, product=product)

# Order Routes
@app.route('/order-history')
@login_required
def order_history():
    user_id = session['user_id']
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    return render_template('order_history.html', orders=orders)

@app.route('/seller/order-history')
@login_required
def seller_order_history():
    """Seller's order history - orders they made as a buyer"""
    user = User.query.get(session['user_id'])
    if user.role != 'seller':
        flash('Access denied. This page is for sellers only.', 'error')
        return redirect(url_for('home'))
    
    # Get orders where the seller is the buyer (not their own products)
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    return render_template('seller_order_history.html', orders=orders)

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    session_id = get_session_id()
    cart_items = CartItem.query.filter_by(session_id=session_id).all()
    
    if not cart_items:
        flash('Your cart is empty. Add some items before checkout.', 'warning')
        return redirect(url_for('shop'))
    
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    shipping_threshold = Decimal("50.00")
    shipping_cost = Decimal("5.99")
    tax_rate = Decimal("0.08")
    
    shipping = Decimal("0.00") if subtotal >= shipping_threshold else shipping_cost
    tax = subtotal * tax_rate
    total = subtotal + shipping + tax
    
    return render_template('checkout.html', 
                         cart_items=cart_items,
                         subtotal=subtotal,
                         shipping=shipping,
                         tax=tax,
                         total=total,
                         stripe_pk=app.config['STRIPE_PUBLISHABLE_KEY'])

# Stripe Routes
@app.route('/create-payment-intent', methods=['POST'])
@login_required
def create_payment_intent():
    try:
        session_id = get_session_id()
        cart_items = CartItem.query.filter_by(session_id=session_id).all()
        
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Calculate total
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        shipping_threshold = Decimal("50.00")
        shipping_cost = Decimal("5.99")
        tax_rate = Decimal("0.08")
        
        shipping = Decimal("0.00") if subtotal >= shipping_threshold else shipping_cost
        tax = subtotal * tax_rate
        total = subtotal + shipping + tax
        
        # Convert to cents for Stripe (ensure it's an integer)
        amount_in_cents = int(total * 100)
        
        print(f"Creating payment intent for amount: {amount_in_cents} cents (${total})")  # Debug log
        
        # Verify Stripe key is set
        if not stripe.api_key:
            print("Stripe API key not set!")
            return jsonify({'error': 'Payment system not configured'}), 500
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency='usd',
            automatic_payment_methods={
                'enabled': True,
            },
            metadata={
                'user_id': str(session['user_id']),
                'session_id': session_id,
                'order_type': 'online_purchase'
            }
        )
        
        print(f"Payment intent created successfully: {intent.id}")  # Debug log
        
        return jsonify({
            'client_secret': intent.client_secret
        })
        
    except stripe.error.StripeError as e:
        print(f"Stripe error: {str(e)}")
        return jsonify({'error': f'Payment system error: {str(e)}'}), 500
    except Exception as e:
        print(f"General error in create_payment_intent: {str(e)}")
        import traceback
        traceback.print_exc()  # This will help debug the exact error
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/process-stripe-payment', methods=['POST'])
@login_required
def process_stripe_payment():
    try:
        data = request.get_json()
        payment_intent_id = data.get('payment_intent_id')
        shipping_info = data.get('shipping_info')
        
        # Verify payment intent
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status != 'succeeded':
            return jsonify({'success': False, 'error': 'Payment not completed'}), 400
        
        session_id = get_session_id()
        cart_items = CartItem.query.filter_by(session_id=session_id).all()
        
        if not cart_items:
            return jsonify({'success': False, 'error': 'Cart is empty'}), 400
        
        # Calculate totals
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        shipping_threshold = Decimal("50.00")
        shipping_cost = Decimal("5.99")
        tax_rate = Decimal("0.08")
        
        shipping = Decimal("0.00") if subtotal >= shipping_threshold else shipping_cost
        tax = subtotal * tax_rate
        total = subtotal + shipping + tax
        
        # Create order
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        order = Order(
            order_number=order_number,
            user_id=session['user_id'],
            total_amount=total,
            status='confirmed'
        )
        db.session.add(order)
        db.session.flush()
        
        # Create order items and update stock
        for cart_item in cart_items:
            if cart_item.product.stock_quantity < cart_item.quantity:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'{cart_item.product.name} is out of stock'}), 400
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)
            cart_item.product.stock_quantity -= cart_item.quantity
        
        # Clear cart
        for cart_item in cart_items:
            db.session.delete(cart_item)
        
        db.session.commit()
        
        send_order_confirmation_email(order)
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'order_number': order_number
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.filter_by(id=order_id, user_id=session['user_id']).first_or_404()
    return render_template('order_confirmation.html', order=order)

# Order Management Routes
@app.route('/api/order/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    """Cancel an order if it's still pending"""
    try:
        order = Order.query.filter_by(id=order_id, user_id=session['user_id']).first_or_404()
        
        if order.status not in ['pending', 'confirmed']:
            return jsonify({
                'success': False,
                'message': 'Order cannot be cancelled at this stage. Orders can only be cancelled when pending or confirmed.'
            }), 400
        
        # Restore stock quantities
        for item in order.order_items:
            item.product.stock_quantity += item.quantity
        
        # Update order status
        order.status = 'cancelled'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order cancelled successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to cancel order'
        }), 500

@app.route('/api/order/<int:order_id>/track')
@login_required
def track_order(order_id):
    """Get order tracking information"""
    order = Order.query.filter_by(id=order_id, user_id=session['user_id']).first_or_404()
    
    # Create tracking stages based on actual order status
    tracking_stages = []
    
    # Always show these initial stages
    tracking_stages.append({'status': 'Order Placed', 'date': order.created_at, 'completed': True})
    tracking_stages.append({'status': 'Payment Confirmed', 'date': order.created_at, 'completed': True})
    
    # Add stages based on current status
    if order.status == 'cancelled':
        tracking_stages.append({'status': 'Order Cancelled', 'date': None, 'completed': True})
    elif order.status == 'refund_approved':
        tracking_stages.append({'status': 'Order Cancelled', 'date': None, 'completed': True})
        tracking_stages.append({'status': 'Refund Approved', 'date': None, 'completed': True})
    else:
        # Normal order flow
        tracking_stages.append({'status': 'Order Confirmed', 'date': None, 'completed': order.status in ['confirmed', 'processing', 'shipped', 'delivered']})
        tracking_stages.append({'status': 'Processing', 'date': None, 'completed': order.status in ['processing', 'shipped', 'delivered']})
        tracking_stages.append({'status': 'Shipped', 'date': None, 'completed': order.status in ['shipped', 'delivered']})
        tracking_stages.append({'status': 'Delivered', 'date': None, 'completed': order.status == 'delivered'})
    
    return jsonify({
        'order_number': order.order_number,
        'status': order.status,
        'tracking_stages': tracking_stages,
        'estimated_delivery': '3-5 business days'
    })

@app.route('/api/reorder/<int:order_id>', methods=['POST'])
@login_required
def reorder(order_id):
    """Add all items from a previous order to cart"""
    try:
        order = Order.query.filter_by(id=order_id, user_id=session['user_id']).first_or_404()
        session_id = get_session_id()
        items_added = 0
        
        for order_item in order.order_items:
            # Check if product is still available
            if order_item.product.stock_quantity > 0:
                # Check if item already in cart
                cart_item = CartItem.query.filter_by(
                    session_id=session_id,
                    product_id=order_item.product_id
                ).first()
                
                quantity_to_add = min(order_item.quantity, order_item.product.stock_quantity)
                
                if cart_item:
                    cart_item.quantity += quantity_to_add
                else:
                    cart_item = CartItem(
                        session_id=session_id,
                        product_id=order_item.product_id,
                        quantity=quantity_to_add
                    )
                    db.session.add(cart_item)
                
                items_added += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{items_added} items added to cart',
            'cart_count': get_cart_count()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to reorder items'
        }), 500

# Sales Analytics Routes
@app.route('/api/seller/sales-trend')
@seller_required
def seller_sales_trend():
    """Get sales trend data for the last 30 days"""
    from datetime import datetime, timedelta
    from sqlalchemy import func, distinct
    
    user_id = session['user_id']
    
    # Get sales data for the last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=29)  # 30 days total including today
    
    # Query daily sales (revenue) for seller's products
    daily_sales = (
        db.session.query(
            func.date(Order.created_at).label('date'),
            func.sum(OrderItem.price * OrderItem.quantity).label('revenue'),
            func.count(distinct(Order.id)).label('orders')
        )
        .join(OrderItem, Order.id == OrderItem.order_id)
        .join(Product, OrderItem.product_id == Product.id)
        .filter(
            Product.seller_id == user_id,
            func.date(Order.created_at) >= start_date,
            func.date(Order.created_at) <= end_date,
            Order.status.in_(['confirmed', 'processing', 'shipped', 'delivered'])  # Only successful orders
        )
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )
    
    # Create a complete date range with zero values for days without sales
    sales_dict = {sale.date: {'revenue': float(sale.revenue or 0), 'orders': sale.orders} for sale in daily_sales}
    
    # Generate all dates in range
    current_date = start_date
    dates = []
    revenues = []
    orders = []
    
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        if current_date in sales_dict:
            revenues.append(sales_dict[current_date]['revenue'])
            orders.append(sales_dict[current_date]['orders'])
        else:
            revenues.append(0)
            orders.append(0)
        current_date += timedelta(days=1)
    
    # Calculate some summary statistics
    total_revenue = sum(revenues)
    total_orders = sum(orders)
    avg_daily_revenue = total_revenue / 30 if total_revenue > 0 else 0
    
    # Calculate trend (comparing last 15 days vs previous 15 days)
    last_15_days_revenue = sum(revenues[-15:])
    prev_15_days_revenue = sum(revenues[:15])
    
    if prev_15_days_revenue > 0:
        trend_percentage = ((last_15_days_revenue - prev_15_days_revenue) / prev_15_days_revenue) * 100
    else:
        trend_percentage = 100 if last_15_days_revenue > 0 else 0
    
    return jsonify({
        'dates': dates,
        'revenues': revenues,
        'orders': orders,
        'summary': {
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'avg_daily_revenue': avg_daily_revenue,
            'trend_percentage': round(trend_percentage, 1),
            'trend_direction': 'up' if trend_percentage >= 0 else 'down'
        }
    })

# Seller Order Management Routes
@app.route('/api/seller/orders')
@seller_required
def seller_orders():
    """Get all orders for seller's products"""
    user_id = session['user_id']
    
    # Get orders that contain seller's products
    orders = (
        db.session.query(Order)
        .join(OrderItem)
        .join(Product)
        .filter(Product.seller_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    
    orders_data = []
    for order in orders:
        # Get only the items from this seller
        seller_items = [
            item for item in order.order_items 
            if item.product.seller_id == user_id
        ]
        
        if seller_items:  # Only include orders with seller's products
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.user.username,
                'customer_email': order.user.email,
                'status': order.status,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
                'total_amount': float(sum(item.price * item.quantity for item in seller_items)),
                'items': [{
                    'id': item.id,
                    'product_name': item.product.name,
                    'product_image': item.product.image_url,
                    'quantity': item.quantity,
                    'price': float(item.price)
                } for item in seller_items]
            })
    
    return jsonify({'orders': orders_data})

@app.route('/api/seller/order/<int:order_id>/update-status', methods=['POST'])
@seller_required
def update_order_status(order_id):
    """Update order status by seller"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        # Validate status
        valid_statuses = ['confirmed', 'processing', 'shipped', 'delivered']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'message': 'Invalid status'
            }), 400
        
        # Get order and verify seller has products in it
        order = Order.query.get_or_404(order_id)
        user_id = session['user_id']
        
        # Check if seller has products in this order
        seller_has_products = any(
            item.product.seller_id == user_id 
            for item in order.order_items
        )
        
        if not seller_has_products:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        
        # Don't allow status updates on cancelled orders
        if order.status == 'cancelled':
            return jsonify({
                'success': False,
                'message': 'Cannot update cancelled orders'
            }), 400
        
        # Update order status
        order.status = new_status
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Order status updated to {new_status}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to update order status'
        }), 500

@app.route('/api/seller/order/<int:order_id>/approve-refund', methods=['POST'])
@seller_required
def approve_refund(order_id):
    """Approve refund for cancelled order"""
    try:
        # Get order and verify seller has products in it
        order = Order.query.get_or_404(order_id)
        user_id = session['user_id']
        
        # Check if seller has products in this order
        seller_has_products = any(
            item.product.seller_id == user_id 
            for item in order.order_items
        )
        
        if not seller_has_products:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        
        # Only allow refund approval for cancelled orders
        if order.status != 'cancelled':
            return jsonify({
                'success': False,
                'message': 'Order is not cancelled'
            }), 400
        
        # Update order status to indicate refund approved
        order.status = 'refund_approved'
        db.session.commit()
        
        # Here you would typically integrate with payment processor to issue refund
        # For now, we'll just update the status
        
        return jsonify({
            'success': True,
            'message': 'Refund approved successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to approve refund'
        }), 500

# Email Notification Function
def send_order_confirmation_email(order):
    """Send order confirmation email to customer"""
    try:
        user = order.user
        subject = f"Order Confirmation - {order.order_number}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #ea580c; margin-bottom: 10px;">Only</h1>
                    <h2 style="color: #333;">Order Confirmation</h2>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0;">Hi {user.username},</h3>
                    <p>Thank you for your order! We've received your order and it's being processed.</p>
                    
                    <div style="margin: 20px 0;">
                        <strong>Order Number:</strong> {order.order_number}<br>
                        <strong>Order Date:</strong> {order.created_at.strftime('%B %d, %Y')}<br>
                        <strong>Total Amount:</strong> <span style="color: #ea580c; font-weight: bold;">${order.total_amount:.2f}</span>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3>Order Items:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Product</th>
                                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Qty</th>
                                <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">Price</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for item in order.order_items:
            html_body += f"""
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd;">{item.product.name}</td>
                                <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{item.quantity}</td>
                                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">${item.price * item.quantity:.2f}</td>
                            </tr>
            """
        
        html_body += f"""
                        </tbody>
                    </table>
                </div>
                
                <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="margin-top: 0; color: #28a745;">What's Next?</h4>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>Your order is being prepared for shipment</li>
                        <li>You'll receive tracking information within 1-2 business days</li>
                        <li>Estimated delivery: 3-5 business days</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <p>Thank you for shopping with Only!</p>
                    <p style="color: #666; font-size: 14px;">
                        If you have any questions, please contact us at support@only.com
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(subject, recipients=[user.email], html=html_body)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default categories if they don't exist
        if not Category.query.first():
            categories = [
                Category(name='Electronics', description='Electronic devices and gadgets'),
                Category(name='Clothing', description='Fashion and apparel'),
                Category(name='Home & Garden', description='Home improvement and garden supplies'),
                Category(name='Books', description='Books and educational materials'),
                Category(name='Sports', description='Sports and outdoor equipment')
            ]
            for category in categories:
                db.session.add(category)
            db.session.commit()
            print("Default categories created!")
        
        print("Database tables created successfully!")
    
app.run(port="5002",debug=True)