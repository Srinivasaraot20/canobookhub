from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    full_name = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # publisher, author, vendor, student
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    bio = db.Column(db.Text)  # Author biography
    profile_image = db.Column(db.String(255))  # Author profile image
    awards = db.Column(db.Text)  # Author awards/recognitions

    # Relationships
    books = db.relationship('Book', backref='author', lazy=True, foreign_keys='Book.author_id')
    orders = db.relationship('Order', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    documents = db.relationship('Document', backref='user', lazy=True, foreign_keys='Document.user_id')
    wishlist_items = db.relationship('Wishlist', back_populates='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(17), unique=True)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    wholesale_price = db.Column(db.Float)
    stock = db.Column(db.Integer, default=0)
    pages = db.Column(db.Integer)
    edition = db.Column(db.String(50))
    publisher_name = db.Column(db.String(100))
    subject = db.Column(db.String(100))
    exam_type = db.Column(db.String(50))  # UPSC, SSC, JEE, NEET, etc.
    cover_image = db.Column(db.String(200))
    sample_pdf = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(50), default='English')
    category = db.Column(db.String(100))  # Fiction, Non-fiction, Academic, etc.
    keywords = db.Column(db.Text)  # Comma-separated keywords for recommendations
    view_count = db.Column(db.Integer, default=0)
    amazon_link = db.Column(db.String(500))  # Amazon or external purchase link

    # Foreign keys
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    publisher_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    order_items = db.relationship('OrderItem', backref='book', lazy=True)
    reviews = db.relationship('Review', backref='book', lazy=True)
    royalties = db.relationship('Royalty', backref='book', lazy=True)
    cart_items = db.relationship('CartItem', back_populates='book', lazy=True)
    wishlist_items = db.relationship('Wishlist', back_populates='book', lazy=True, cascade='all, delete-orphan')

    @property
    def avg_rating(self):
        ratings = [r.rating for r in self.reviews]
        return round(sum(ratings) / len(ratings), 1) if ratings else 0

    @property
    def total_reviews(self):
        return len([r for r in self.reviews])

    def __repr__(self):
        return f'<Book {self.title}>'


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, shipped, delivered, cancelled
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    payment_method = db.Column(db.String(50))
    shipping_address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<OrderItem {self.id}>'


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    helpful_votes = db.Column(db.Integer, default=0)
    is_approved = db.Column(db.Boolean, default=True)
    is_flagged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reply = db.Column(db.Text)  # Author's reply to the review

    def __repr__(self):
        return f'<Review {self.id}>'


class ReviewHelpful(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='helpful_reviews')
    review = db.relationship('Review', backref='helpful_marks')

    def __repr__(self):
        return f'<ReviewHelpful {self.id}>'


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))  # order, review, system, etc.
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Optional links
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))

    # Relationships
    user = db.relationship('User', backref='notifications')
    order = db.relationship('Order', backref='notifications')
    book = db.relationship('Book', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.id}>'


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Category {self.name}>'


class Analytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)  # page_view, book_view, search, purchase
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    search_query = db.Column(db.String(200))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='analytics')
    book = db.relationship('Book', backref='analytics')

    def __repr__(self):
        return f'<Analytics {self.event_type}>'


class Royalty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    percentage = db.Column(db.Float, nullable=False)  # Royalty percentage
    sales_count = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    last_payment_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    author = db.relationship('User', backref='royalty_records')

    def __repr__(self):
        return f'<Royalty {self.id}>'


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    document_type = db.Column(db.String(50))  # contract, agreement, pan, aadhaar, etc.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))  # Optional: link to specific book
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    uploader = db.relationship('User', foreign_keys=[uploaded_by], backref='uploaded_documents')

    def __repr__(self):
        return f'<Document {self.title}>'


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='cart_items')
    book = db.relationship('Book', back_populates='cart_items')

    def __repr__(self):
        return f'<CartItem {self.id}>'

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='wishlist_items')
    book = db.relationship('Book', back_populates='wishlist_items')