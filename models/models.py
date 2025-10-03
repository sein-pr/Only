# models/models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='buyer')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Profile fields
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))  # Keep for backward compatibility
    phone_country_code = db.Column(db.String(5))  # e.g., +1, +44, +91
    phone_number = db.Column(db.String(15))  # The actual phone number
    address = db.Column(db.Text)  # Keep for backward compatibility
    address_line1 = db.Column(db.String(100))
    address_line2 = db.Column(db.String(100))
    city = db.Column(db.String(50))
    state_province = db.Column(db.String(50))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(50))
    avatar_url = db.Column(db.String(200))
    
    # Company/Business fields (mainly for sellers)
    company_name = db.Column(db.String(100))
    company_description = db.Column(db.Text)
    company_logo_url = db.Column(db.String(200))
    company_website = db.Column(db.String(200))
    company_phone = db.Column(db.String(20))  # Keep for backward compatibility
    company_phone_country_code = db.Column(db.String(5))
    company_phone_number = db.Column(db.String(15))
    company_address = db.Column(db.Text)  # Keep for backward compatibility
    company_address_line1 = db.Column(db.String(100))
    company_address_line2 = db.Column(db.String(100))
    company_city = db.Column(db.String(50))
    company_state_province = db.Column(db.String(50))
    company_postal_code = db.Column(db.String(20))
    company_country = db.Column(db.String(50))

    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True)
    products = db.relationship('Product', backref='seller', lazy=True)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(200))
    additional_images = db.Column(db.JSON)  # Store array of additional image URLs
    status = db.Column(db.String(20), default='active')  # active, inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, shipped, delivered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    # Foreign Keys
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    save_for_later = db.Column(db.Boolean, default=False)  # New field for save for later
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', backref='cart_items')


class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='wishlist_items')
    product = db.relationship('Product', backref='wishlist_items')

    # Ensure unique user-product combination
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_product_wishlist'),)


class ProductView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable for guest views
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    view_type = db.Column(db.String(20), nullable=False)  # 'quick_view' or 'full_detail'
    ip_address = db.Column(db.String(45))  # For tracking guest views
    user_agent = db.Column(db.String(500))  # Browser info
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='product_views')
    product = db.relationship('Product', backref='product_views')


class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref='password_reset_tokens')