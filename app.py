from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
# from flask_wtf.csrf import exempt
from wtforms import StringField, PasswordField, TextAreaField, DecimalField, IntegerField, SelectField, FileField
from wtforms.validators import DataRequired, Email, Length, NumberRange
from models.models import db, User, Category, Product, Order, OrderItem, CartItem
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
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
            
            flash(f'Welcome back, {user.username}!', 'success')
            
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
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('home'))

# Main Routes
@app.route('/')
def home():
    # Get featured products (latest 8 products)
    featured_products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
    categories = Category.query.all()
    return render_template('home.html', featured_products=featured_products, categories=categories)

@app.route('/shop')
def shop():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    
    query = Product.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(Product.name.contains(search))
    
    products = query.paginate(
        page=page, per_page=12, error_out=False
    )
    
    categories = Category.query.all()
    return render_template('shop.html', products=products, categories=categories, 
                         current_category=category_id, search=search)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id
    ).limit(4).all()
    return render_template('product_detail.html', product=product, related_products=related_products)

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
def add_to_wishlist(product_id):
    # For now, just return success - implement full wishlist later
    return jsonify({
        'success': True,
        'message': 'Added to wishlist!'
    })

@app.route('/api/product/<int:product_id>/quick-view')
def product_quick_view(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('partials/quick_view.html', product=product)

# Seller Routes
@app.route('/seller/dashboard')
@seller_required
def seller_dashboard():
    user_id = session['user_id']
    
    # Get seller statistics
    total_products = Product.query.filter_by(seller_id=user_id).count()
    total_orders = db.session.query(Order).join(OrderItem).join(Product).filter(
        Product.seller_id == user_id
    ).count()
    
    # Get recent products
    recent_products = Product.query.filter_by(seller_id=user_id).order_by(
        Product.created_at.desc()
    ).limit(5).all()
    
    return render_template('seller/dashboard.html', 
                         total_products=total_products,
                         total_orders=total_orders,
                         recent_products=recent_products)

@app.route('/seller/products')
@seller_required
def seller_products():
    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    
    products = Product.query.filter_by(seller_id=user_id).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('seller/products.html', products=products)

@app.route('/seller/add-product', methods=['GET', 'POST'])
@seller_required
def add_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        # Handle file upload
        image_url = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            if filename:
                filename = f"{uuid.uuid4()}_{filename}"
                form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = f"/static/uploads/{filename}"
        
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock_quantity=form.stock_quantity.data,
            category_id=form.category_id.data,
            seller_id=session['user_id'],
            image_url=image_url
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('seller_products'))
    
    return render_template('seller/add_product.html', form=form)

# Order Routes
@app.route('/order-history')
@login_required
def order_history():
    user_id = session['user_id']
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    return render_template('order_history.html', orders=orders)

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
                'message': 'Order cannot be cancelled at this stage'
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
    
    # Simulate tracking stages
    tracking_stages = [
        {'status': 'Order Placed', 'date': order.created_at, 'completed': True},
        {'status': 'Payment Confirmed', 'date': order.created_at, 'completed': True},
        {'status': 'Processing', 'date': None, 'completed': order.status in ['shipped', 'delivered']},
        {'status': 'Shipped', 'date': None, 'completed': order.status in ['shipped', 'delivered']},
        {'status': 'Delivered', 'date': None, 'completed': order.status == 'delivered'}
    ]
    
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
    
    app.run(debug=True)