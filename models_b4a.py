from back4app_client import Back4AppClient
import os
from datetime import datetime

client = Back4AppClient()

class Field:
    def __init__(self, name=None):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance._data.get(self.name)

    def __set__(self, instance, value):
        instance._data[self.name] = value

    def __eq__(self, other):
        return {'field': self.name, 'op': '$eq', 'value': other}
    
    def __ne__(self, other):
        return {'field': self.name, 'op': '$ne', 'value': other}
    
    def __gt__(self, other):
        return {'field': self.name, 'op': '$gt', 'value': other}
    
    def __ge__(self, other):
        return {'field': self.name, 'op': '$gte', 'value': other}
    
    def __lt__(self, other):
        return {'field': self.name, 'op': '$lt', 'value': other}
    
    def __le__(self, other):
        return {'field': self.name, 'op': '$lte', 'value': other}
    
    def ilike(self, pattern):
        # Parse supports regex for string matching
        # Convert SQL LIKE %pattern% to Regex
        regex = pattern.replace('%', '.*')
        return {'field': self.name, 'op': '$regex', 'value': regex, 'options': 'i'}
    
    def desc(self):
        return f'-{self.name}'
    
    def asc(self):
        return self.name

class Query:
    def __init__(self, model_class):
        self.model_class = model_class
        self.where = {}
        self._order = None
        self._limit = None
        self._skip = 0

    def filter_by(self, **kwargs):
        self.where.update(kwargs)
        return self

    def filter(self, *criteria):
        for criterion in criteria:
            if not isinstance(criterion, dict):
                continue # Should not happen if using Field operators
                
            field = criterion['field']
            op = criterion['op']
            val = criterion['value']
            
            if op == '$eq':
                self.where[field] = val
            elif op == '$regex':
                self.where[field] = {'$regex': val, '$options': criterion.get('options', '')}
            else:
                if field not in self.where or not isinstance(self.where[field], dict):
                     self.where[field] = {}
                if isinstance(self.where[field], dict):
                    self.where[field][op] = val
                else:
                    # Conflict: it was an equality check before
                    self.where[field] = {'$eq': self.where[field], op: val}
        return self

    def order_by(self, *args):
        # args are strings like '-created_at' or 'created_at'
        # or Field objects calling .desc() or .asc()
        orders = []
        for arg in args:
            if isinstance(arg, str):
                orders.append(arg)
            else:
                # Assuming it's a Field object or result of desc/asc
                orders.append(str(arg))
        self._order = ','.join(orders)
        return self

    def limit(self, limit):
        self._limit = limit
        return self

    def offset(self, offset):
        self._skip = offset
        return self

    def all(self):
        result = client.query(self.model_class.__name__, where=self.where, order=self._order, limit=self._limit, skip=self._skip)
        return [self.model_class(r) for r in result.get('results', [])]

    def first(self):
        self._limit = 1
        items = self.all()
        return items[0] if items else None

    def get(self, object_id):
        data = client.get(self.model_class.__name__, object_id)
        if data:
            return self.model_class(data)
        return None
    
    def get_or_404(self, object_id):
        item = self.get(object_id)
        if not item:
            from flask import abort
            abort(404)
        return item
    
    def count(self):
        # Parse count query
        result = client.query(self.model_class.__name__, where=self.where, limit=0, count=1)
        return result.get('count', 0)

    def paginate(self, page=1, per_page=20, error_out=True):
        self._limit = per_page
        self._skip = (page - 1) * per_page
        items = self.all()
        total = self.count() # This is expensive, maybe optimize?
        
        class Pagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1
                self.next_num = page + 1
                
            def iter_pages(self):
                # Simple implementation
                return range(1, self.pages + 1)

        return Pagination(items, page, per_page, total)

class BaseModel:
    objectId = Field('objectId')
    createdAt = Field('createdAt')
    updatedAt = Field('updatedAt')

    def __init__(self, data=None, **kwargs):
        self._data = data or {}
        self._data.update(kwargs)
        
    @property
    def id(self):
        return self.objectId
        
    @id.setter
    def id(self, value):
        self.objectId = value

    def save(self):
        if self.objectId:
            # Update
            # Filter out system fields
            data = {k: v for k, v in self._data.items() if k not in ['objectId', 'createdAt', 'updatedAt']}
            client.update(self.__class__.__name__, self.objectId, data)
        else:
            # Create
            resp = client.create(self.__class__.__name__, self._data)
            self.objectId = resp.get('objectId')
            self.createdAt = resp.get('createdAt')

    def delete(self):
        if self.objectId:
            client.delete(self.__class__.__name__, self.objectId)

    @classmethod
    @property
    def query(cls):
        return Query(cls)

# Mock DB Session
class Session:
    def __init__(self):
        self._new = []
        self._deleted = []

    def add(self, obj):
        self._new.append(obj)

    def delete(self, obj):
        self._deleted.append(obj)

    def commit(self):
        for obj in self._new:
            obj.save()
        for obj in self._deleted:
            obj.delete()
        self._new = []
        self._deleted = []
        
    def rollback(self):
        self._new = []
        self._deleted = []

class DB:
    def __init__(self):
        self.session = Session()
        self.Model = BaseModel
        
    def init_app(self, app):
        pass
        
    def create_all(self):
        pass # No schema creation needed for Parse
        
    def relationship(self, *args, **kwargs):
        pass # Ignored for now
        
    def Column(self, *args, **kwargs):
        pass # Ignored
        
    def Integer(self): pass
    def String(self, *args): pass
    def Text(self): pass
    def Boolean(self): pass
    def DateTime(self): pass
    def Numeric(self, *args): pass
    def JSON(self): pass
    def ForeignKey(self, *args): pass

db = DB()

# Define Models mirroring models.py
class User(BaseModel):
    username = Field('username')
    email = Field('email')
    password_hash = Field('password_hash')
    role = Field('role')
    first_name = Field('first_name')
    last_name = Field('last_name')
    phone = Field('phone')
    address = Field('address')
    # ... other fields can be dynamic in NoSQL, so we don't strictly need to define them all if we use _data
    # But for query filters to work with Field objects, we should define them.
    
    # We can use __getattr__ to handle dynamic fields for getting/setting, 
    # but for class-level filtering (User.email == ...), we need the descriptors.
    
    # Let's define the ones used in queries
    
class Category(BaseModel):
    name = Field('name')
    description = Field('description')

class Product(BaseModel):
    name = Field('name')
    description = Field('description')
    price = Field('price')
    stock_quantity = Field('stock_quantity')
    image_url = Field('image_url')
    additional_images = Field('additional_images')
    status = Field('status')
    category_id = Field('category_id') # Storing ID as string now
    seller_id = Field('seller_id')
    created_at = Field('createdAt') # Map to system field

class Order(BaseModel):
    order_number = Field('order_number')
    total_amount = Field('total_amount')
    status = Field('status')
    user_id = Field('user_id')

class OrderItem(BaseModel):
    quantity = Field('quantity')
    price = Field('price')
    order_id = Field('order_id')
    product_id = Field('product_id')
    
    @property
    def product(self):
        if self.product_id:
            return Product.query.get(self.product_id)
        return None

class CartItem(BaseModel):
    session_id = Field('session_id')
    product_id = Field('product_id')
    quantity = Field('quantity')
    save_for_later = Field('save_for_later')
    
    @property
    def product(self):
        if self.product_id:
            return Product.query.get(self.product_id)
        return None

class Wishlist(BaseModel):
    user_id = Field('user_id')
    product_id = Field('product_id')

class ProductView(BaseModel):
    user_id = Field('user_id')
    product_id = Field('product_id')
    view_type = Field('view_type')
    ip_address = Field('ip_address')
    user_agent = Field('user_agent')

class PasswordResetToken(BaseModel):
    user_id = Field('user_id')
    token = Field('token')
    expires_at = Field('expires_at') # Needs to handle datetime serialization
    used = Field('used')

# Helper to handle relationships that were backrefs
# In SQLAlchemy: product.seller
# In here: we need to implement it manually or use a property
# User.products -> Product.query.filter_by(seller_id=self.id).all()

# Monkey patch or add methods to classes
def get_products(self):
    return Product.query.filter_by(seller_id=self.id).all()
User.products = property(get_products)

def get_seller(self):
    return User.query.get(self.seller_id)
Product.seller = property(get_seller)

def get_category(self):
    return Category.query.get(self.category_id)
Product.category = property(get_category)

# ... add others as needed
