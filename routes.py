from flask import render_template, request, redirect, url_for, flash, session, jsonify, abort, send_file, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_
import os
import uuid
from datetime import datetime, timedelta

from app import app, db
from app import socketio
from models import User, Book, Order, OrderItem, Review, Royalty, Document, CartItem, Wishlist, Notification
from forms import LoginForm, RegisterForm, BookForm, DocumentForm, ReviewForm, RoyaltyForm, CheckoutForm
from utils import allowed_file, generate_order_number, calculate_royalty
from email_service import email_service

# Import advanced routes
import advanced_routes

# Removed any remaining import of firebase_admin

import razorpay
from flask import request, jsonify

# Initialize Razorpay client (using Razorpay public test credentials for demo)
razorpay_client = razorpay.Client(auth=("rzp_test_1DP5mmOlF5G5ag", "1234567890qwertyuiopzxcvbnm"))


@app.route('/')
def index():
    # Get featured books
    featured_books = Book.query.filter_by(is_active=True).order_by(Book.created_at.desc()).limit(8).all()
    
    # Get books by category
    upsc_books = Book.query.filter_by(exam_type='UPSC', is_active=True).limit(4).all()
    jee_books = Book.query.filter_by(exam_type='JEE', is_active=True).limit(4).all()
    neet_books = Book.query.filter_by(exam_type='NEET', is_active=True).limit(4).all()
    ssc_books = Book.query.filter_by(exam_type='SSC', is_active=True).limit(4).all()
    
    return render_template('index.html', 
                         featured_books=featured_books,
                         upsc_books=upsc_books,
                         jee_books=jee_books,
                         neet_books=neet_books,
                         ssc_books=ssc_books)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'error')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists', 'error')
            return render_template('register.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data,
            phone=form.phone.data,
            address=form.address.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'publisher':
        return redirect(url_for('publisher_dashboard'))
    elif current_user.role == 'author':
        return redirect(url_for('author_dashboard'))
    elif current_user.role == 'vendor':
        return redirect(url_for('vendor_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))


@app.route('/dashboard/publisher')
@login_required
def publisher_dashboard():
    if current_user.role != 'publisher':
        abort(403)
    
    # Get statistics
    total_books = Book.query.count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(Order.payment_status == 'paid').scalar() or 0
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('dashboard/publisher.html', 
                         total_books=total_books,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders)


@app.route('/dashboard/author')
@login_required
def author_dashboard():
    if current_user.role != 'author':
        abort(403)
    
    # Get author's books and royalty info
    author_books = Book.query.filter_by(author_id=current_user.id).all()
    royalty_records = Royalty.query.filter_by(author_id=current_user.id).all()
    total_earnings = sum(r.total_earnings for r in royalty_records)
    
    return render_template('dashboard/author.html', 
                         author_books=author_books,
                         royalty_records=royalty_records,
                         total_earnings=total_earnings)


@app.route('/dashboard/vendor')
@login_required
def vendor_dashboard():
    if current_user.role not in ['vendor', 'vendor_distributor']:
        abort(403)
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    # Total books
    total_books = Book.query.filter_by(publisher_id=current_user.id).count()
    # Today's orders and revenue
    todays_orders = OrderItem.query.join(Order).filter(
        OrderItem.book.has(publisher_id=current_user.id),
        db.func.date(Order.created_at) == today
    ).all()
    todays_order_count = len(todays_orders)
    todays_revenue = sum(item.price * item.quantity for item in todays_orders)
    # Low-stock books
    low_stock_books = Book.query.filter_by(publisher_id=current_user.id).filter(Book.stock < 5).all()
    return render_template(
        'dashboard/vendor_dashboard.html',
        total_books=total_books,
        todays_order_count=todays_order_count,
        todays_revenue=todays_revenue,
        low_stock_books=low_stock_books
    )

@app.route('/vendor/sales_data')
@login_required
def vendor_sales_data():
    if current_user.role not in ['vendor', 'vendor_distributor']:
        abort(403)
    from datetime import datetime, timedelta
    import calendar
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=29)
    sales = db.session.query(
        db.func.date(Order.created_at),
        db.func.sum(OrderItem.price * OrderItem.quantity)
    ).join(OrderItem, Order.id == OrderItem.order_id)\
    .filter(OrderItem.book.has(publisher_id=current_user.id))\
    .filter(Order.created_at >= start_date)\
    .group_by(db.func.date(Order.created_at))\
    .all()
    # Fill missing days with 0
    sales_dict = {str(date): float(amount) for date, amount in sales}
    labels = [(start_date + timedelta(days=i)).isoformat() for i in range(30)]
    data = [sales_dict.get(day, 0) for day in labels]
    return jsonify({'labels': labels, 'data': data})


@app.route('/dashboard/student')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        abort(403)
    # Get student's orders
    student_orders = Order.query.filter_by(user_id=current_user.id).all()
    # Get all active books
    all_books = Book.query.filter_by(is_active=True).order_by(Book.created_at.desc()).all()
    # Get all reviews submitted by the current user
    my_reviews = Review.query.filter_by(user_id=current_user.id).order_by(Review.created_at.desc()).all()
    return render_template('dashboard/student.html', 
                         student_orders=student_orders,
                         all_books=all_books,
                         my_reviews=my_reviews)


@app.route('/books')
def books():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    exam_type = request.args.get('exam_type', '')
    category = request.args.get('category', '')
    language = request.args.get('language', '')
    author = request.args.get('author', '')
    publisher = request.args.get('publisher', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_rating = request.args.get('min_rating', type=float)
    sort_by = request.args.get('sort_by', 'newest')
    
    query = Book.query.filter_by(is_active=True)
    
    # Apply filters
    if search:
        query = query.filter(or_(
            Book.title.contains(search),
            Book.description.contains(search),
            Book.subject.contains(search),
            Book.keywords.contains(search)
        ))
    
    if exam_type:
        query = query.filter(Book.exam_type == exam_type)
    
    if category:
        query = query.filter(Book.category == category)
    
    if language:
        query = query.filter(Book.language == language)
    
    if author:
        query = query.join(User).filter(User.full_name.contains(author))
    
    if publisher:
        query = query.filter(Book.publisher_name.contains(publisher))
    
    if min_price:
        query = query.filter(Book.price >= min_price)
    
    if max_price:
        query = query.filter(Book.price <= max_price)
    
    # Apply sorting
    if sort_by == 'price_low':
        query = query.order_by(Book.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Book.price.desc())
    elif sort_by == 'title':
        query = query.order_by(Book.title.asc())
    elif sort_by == 'rating':
        # This would require a more complex query with joins
        query = query.order_by(Book.created_at.desc())
    elif sort_by == 'popularity':
        query = query.order_by(Book.view_count.desc())
    else:  # newest
        query = query.order_by(Book.created_at.desc())
    
    books = query.paginate(page=page, per_page=12, error_out=False)
    
    # Get filter options for dropdowns
    categories = db.session.query(Book.category).filter(Book.category.isnot(None)).distinct().all()
    languages = db.session.query(Book.language).filter(Book.language.isnot(None)).distinct().all()
    exam_types = db.session.query(Book.exam_type).filter(Book.exam_type.isnot(None)).distinct().all()
    
    return render_template('books.html', 
                         books=books, 
                         search=search, 
                         exam_type=exam_type,
                         category=category,
                         language=language,
                         author=author,
                         publisher=publisher,
                         min_price=min_price,
                         max_price=max_price,
                         min_rating=min_rating,
                         sort_by=sort_by,
                         categories=[c[0] for c in categories],
                         languages=[l[0] for l in languages],
                         exam_types=[e[0] for e in exam_types])


@app.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    # Validate required fields
    required_fields = ['title', 'price', 'stock', 'author']
    for field in required_fields:
        value = getattr(book, field, None)
        if value is None or (field == 'author' and not book.author):
            flash(f"Book data is incomplete. Missing: {field}", 'error')
            return redirect(url_for('manage_books'))
    
    # Increment view count
    book.view_count += 1
    db.session.commit()
    
    # Get approved reviews sorted by helpful votes
    reviews = Review.query.filter_by(book_id=book_id, is_approved=True).order_by(
        Review.helpful_votes.desc(), Review.created_at.desc()).all()
    
    # Get recommended books
    recommended_books = get_recommended_books(book_id)
    
    # Check if current user has this book in wishlist
    in_wishlist = False
    if current_user.is_authenticated:
        in_wishlist = Wishlist.query.filter_by(user_id=current_user.id, book_id=book_id).first() is not None
    
    return render_template('book_detail.html', 
                         book=book, 
                         reviews=reviews, 
                         recommended_books=recommended_books,
                         in_wishlist=in_wishlist)


@app.route('/authors')
def authors():
    authors = User.query.filter_by(role='author', is_active=True).all()
    return render_template('authors.html', authors=authors)


@app.route('/author/<int:author_id>')
def author_detail(author_id):
    author = User.query.get_or_404(author_id)
    if author.role != 'author':
        abort(404)
    
    author_books = Book.query.filter_by(author_id=author_id, is_active=True).all()
    return render_template('author_detail.html', author=author, author_books=author_books)


@app.route('/add_to_cart/<int:book_id>')
@login_required
def add_to_cart(book_id):
    book = Book.query.get_or_404(book_id)
    
    # Check if item already in cart
    cart_item = CartItem.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=current_user.id, book_id=book_id, quantity=1)
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Book added to cart successfully!', 'success')
    return redirect(url_for('book_detail', book_id=book_id))


@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.quantity * item.book.price for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)


@app.route('/remove_from_cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        abort(403)
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart', 'success')
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('cart'))
    
    form = CheckoutForm()
    total = sum(item.quantity * item.book.price for item in cart_items)
    
    if form.validate_on_submit():
        # Create order
        order = Order(
            order_number=generate_order_number(),
            user_id=current_user.id,
            total_amount=total,
            shipping_address=form.address.data,
            payment_method=form.payment_method.data
        )
        db.session.add(order)
        db.session.flush()  # Get the order ID
        
        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                book_id=cart_item.book_id,
                quantity=cart_item.quantity,
                price=cart_item.book.price
            )
            db.session.add(order_item)
            
            # Update stock
            cart_item.book.stock -= cart_item.quantity
            
            # Update royalty
            calculate_royalty(cart_item.book_id, cart_item.quantity, cart_item.book.price)
        
        # Clear cart
        for cart_item in cart_items:
            db.session.delete(cart_item)
        
        db.session.commit()
        
        # Create notification for user
        from advanced_routes import create_notification
        create_notification(
            current_user.id,
            'Order Placed Successfully',
            f'Your order #{order.order_number} has been placed successfully. Total amount: ₹{order.total_amount}',
            'order',
            order_id=order.id
        )

        # Create notification for all admins (publishers)
        publishers = User.query.filter_by(role='publisher').all()
        item_list = ', '.join([f"{item.book.title} (x{item.quantity})" for item in order.items])
        for admin in publishers:
            create_notification(
                admin.id,
                'New Order Placed',
                f'Order #{order.order_number} placed by {current_user.full_name}. Items: {item_list}. Total: ₹{order.total_amount}. Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}',
            'order',
            order_id=order.id
        )
        
        # Send order confirmation email
        try:
            email_service.send_order_confirmation(current_user, order)
        except Exception as e:
            print(f"Failed to send order confirmation email: {e}")
        
        flash('Order placed successfully! Confirmation email sent.', 'success')
        return redirect(url_for('order_success', order_id=order.id))
    
    return render_template('checkout.html', form=form, cart_items=cart_items, total=total)


@app.route('/order_success/<int:order_id>')
@login_required
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    return render_template('order_success.html', order=order, timedelta=timedelta)


@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    form = BookForm()
    from models import Category, Book
    categories = [c.name for c in Category.query.filter_by(is_active=True).all()]
    form.category.choices = [(c, c) for c in categories]

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    if request.method == 'POST':
        import json
        raw_categories = request.form.get('category', '[]')
        try:
            category_list = [item['value'] for item in json.loads(raw_categories)]
        except Exception:
            category_list = [c.strip() for c in raw_categories.split(',') if c.strip()]
        # Add new categories if needed
        for name in category_list:
            if name and not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name, is_active=True))
        db.session.commit()
        # Ensure price is always set
        price = 0 if form.is_free.data else (form.price.data if form.price.data is not None else 0)

        # Handle cover image upload
        cover_image_file = request.files.get('cover_image')
        cover_image_filename = None
        if cover_image_file and cover_image_file.filename:
            if not allowed_file(cover_image_file.filename):
                flash('Invalid file type for cover image. Allowed: png, jpg, jpeg, gif.', 'danger')
                return render_template('dashboard/add_book.html', form=form, categories=categories)
            filename = secure_filename(cover_image_file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            upload_dir = os.path.join(app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            upload_path = os.path.join(upload_dir, unique_filename)
            cover_image_file.save(upload_path)
            cover_image_filename = unique_filename

        # Create the book
        book = Book(
            title=form.title.data,
            isbn=form.isbn.data,
            description=form.description.data,
            price=price,
            category=', '.join(category_list),
            keywords=form.tags.data,
            language=form.language.data,
            edition=form.edition.data,
            pages=form.pages.data,
            author_id=current_user.id,
            cover_image=cover_image_filename
        )
        db.session.add(book)
        db.session.commit()
        flash('Book published successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('dashboard/add_book.html', form=form, categories=categories)


@app.route('/manage_books')
@login_required
def manage_books():
    if current_user.role != 'publisher':
        abort(403)
    
    books = Book.query.filter_by(is_active=True).all()
    return render_template('dashboard/manage_books.html', books=books)


@app.route('/manage_orders')
@login_required
def manage_orders():
    if current_user.role != 'publisher':
        abort(403)
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('dashboard/manage_orders.html', orders=orders)


@app.route('/royalty')
@login_required
def royalty():
    if current_user.role not in ['publisher', 'author']:
        abort(403)
    
    if current_user.role == 'author':
        royalty_records = Royalty.query.filter_by(author_id=current_user.id).all()
    else:
        royalty_records = Royalty.query.all()
    
    return render_template('dashboard/royalty.html', royalty_records=royalty_records)


@app.route('/documents')
@login_required
def documents():
    if current_user.role == 'publisher':
        documents = Document.query.all()
    else:
        documents = Document.query.filter_by(user_id=current_user.id).all()
    
    return render_template('dashboard/documents.html', documents=documents)


@app.route('/upload_document', methods=['GET', 'POST'])
@login_required
def upload_document():
    form = DocumentForm()
    if form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)
        filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        form.file.data.save(file_path)
        
        document = Document(
            title=form.title.data,
            filename=filename,
            file_path=file_path,
            document_type=form.document_type.data,
            user_id=current_user.id,
            uploaded_by=current_user.id
        )
        
        db.session.add(document)
        db.session.commit()
        
        flash('Document uploaded successfully!', 'success')
        return redirect(url_for('documents'))
    
    return render_template('dashboard/documents.html', form=form)


@app.route('/mark_review_helpful/<int:review_id>')
@login_required
def mark_review_helpful(review_id):
    review = Review.query.get_or_404(review_id)
    
    # Check if user already marked this review as helpful
    existing = ReviewHelpful.query.filter_by(user_id=current_user.id, review_id=review_id).first()
    if existing:
        flash('You have already marked this review as helpful', 'warning')
    else:
        helpful = ReviewHelpful(user_id=current_user.id, review_id=review_id)
        review.helpful_votes += 1
        db.session.add(helpful)
        db.session.commit()
        flash('Review marked as helpful!', 'success')
    
    return redirect(url_for('book_detail', book_id=review.book_id))


@app.route('/add_to_wishlist/<int:book_id>')
@login_required
def add_to_wishlist(book_id):
    book = Book.query.get_or_404(book_id)
    
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if existing:
        flash('Book is already in your wishlist', 'info')
    else:
        wishlist_item = Wishlist(user_id=current_user.id, book_id=book_id)
        db.session.add(wishlist_item)
        db.session.commit()
        flash('Book added to wishlist!', 'success')
    
    return redirect(url_for('book_detail', book_id=book_id))


@app.route('/remove_from_wishlist/<int:book_id>')
@login_required
def remove_from_wishlist(book_id):
    wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        flash('Book removed from wishlist', 'success')
    
    return redirect(url_for('wishlist'))


@app.route('/wishlist')
@login_required
def wishlist():
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist.html', wishlist_items=wishlist_items)


def get_recommended_books(book_id, limit=6):
    """Get recommended books based on current book"""
    current_book = Book.query.get(book_id)
    if not current_book:
        return []
    
    # Get books by same author
    author_books = Book.query.filter(
        Book.author_id == current_book.author_id,
        Book.id != book_id,
        Book.is_active == True
    ).limit(2).all()
    
    # Get books in same category
    category_books = Book.query.filter(
        Book.category == current_book.category,
        Book.id != book_id,
        Book.is_active == True
    ).limit(2).all()
    
    # Get books with similar keywords
    keyword_books = []
    if current_book.keywords:
        keywords = [k.strip() for k in current_book.keywords.split(',')]
        for keyword in keywords[:2]:
            books = Book.query.filter(
                Book.keywords.contains(keyword),
                Book.id != book_id,
                Book.is_active == True
            ).limit(1).all()
            keyword_books.extend(books)
    
    # Combine and deduplicate
    recommended = []
    seen_ids = set()
    
    for book_list in [author_books, category_books, keyword_books]:
        for book in book_list:
            if book.id not in seen_ids and len(recommended) < limit:
                recommended.append(book)
                seen_ids.add(book.id)
    
    # Fill remaining spots with popular books
    if len(recommended) < limit:
        popular_books = Book.query.filter(
            Book.id != book_id,
            Book.is_active == True,
            ~Book.id.in_(seen_ids)
        ).order_by(Book.view_count.desc()).limit(limit - len(recommended)).all()
        recommended.extend(popular_books)
    
    return recommended


@app.route('/orders')
@login_required
def my_orders():
    """View user's orders"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)


@app.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """View order details with tracking"""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and current_user.role != 'publisher':
        abort(403)
    
    # Order tracking timeline
    timeline = []
    timeline.append({
        'status': 'placed',
        'title': 'Order Placed',
        'description': 'Your order has been placed successfully',
        'date': order.created_at,
        'active': True
    })
    
    if order.status in ['confirmed', 'shipped', 'delivered']:
        timeline.append({
            'status': 'confirmed',
            'title': 'Order Confirmed',
            'description': 'Your order has been confirmed and is being prepared',
            'date': order.updated_at,
            'active': True
        })
    
    if order.status in ['shipped', 'delivered']:
        timeline.append({
            'status': 'shipped',
            'title': 'Order Shipped',
            'description': 'Your order has been shipped and is on the way',
            'date': order.updated_at,
            'active': True
        })
    
    if order.status == 'delivered':
        timeline.append({
            'status': 'delivered',
            'title': 'Order Delivered',
            'description': 'Your order has been delivered successfully',
            'date': order.updated_at,
            'active': True
        })
    
    return render_template('order_detail.html', order=order, timeline=timeline)


@app.route('/update_order_status/<int:order_id>/<status>')
@login_required
def update_order_status(order_id, status):
    if current_user.role != 'publisher':
        abort(403)
    
    order = Order.query.get_or_404(order_id)
    order.status = status
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Send status update email
    try:
        email_service.send_order_status_update(order, order.user, status)
    except Exception as e:
        print(f"Failed to send status update email: {e}")
    
    flash(f'Order status updated to {status}. Email notification sent.', 'success')
    return redirect(url_for('manage_orders'))


@app.route('/cancel_order/<int:order_id>')
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    if order.status not in ['pending', 'confirmed', 'shipped']:
        flash('Order cannot be cancelled at this stage.', 'warning')
        return redirect(url_for('my_orders'))
    order.status = 'cancelled'
    order.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Order cancelled successfully.', 'success')
    return redirect(url_for('my_orders'))


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    current_user.full_name = request.form.get('full_name')
    current_user.email = request.form.get('email')
    current_user.phone = request.form.get('phone')
    current_user.address = request.form.get('address')
    
    if current_user.role == 'author':
        current_user.bio = request.form.get('bio')
        current_user.awards = request.form.get('awards')
    
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))


@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('profile'))
    
    if len(new_password) < 6:
        flash('New password must be at least 6 characters long', 'error')
        return redirect(url_for('profile'))
    
    current_user.set_password(new_password)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('profile'))


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/help_center')
def help_center():
    return render_template('help_center.html')

@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms_of_service')
def terms_of_service():
    return render_template('terms_of_service.html')


@app.route('/author/books')
@login_required
def author_books():
    if current_user.role != 'author':
        abort(403)
    books = Book.query.filter_by(author_id=current_user.id).all()
    return render_template('dashboard/author_books.html', books=books)


@app.route('/author/drafts')
@login_required
def author_drafts():
    if current_user.role != 'author':
        abort(403)
    books = Book.query.filter(Book.author_id == current_user.id, Book.status.in_(['draft', 'under_review'])).order_by(Book.updated_at.desc()).all()
    return render_template('dashboard/author_drafts.html', books=books)


@app.route('/author/royalties')
@login_required
def author_royalties():
    if current_user.role != 'author':
        abort(403)
    # Placeholder for now; will add sales/royalty logic later
    return render_template('dashboard/author_royalties.html')


@app.route('/author/reviews')
@login_required
def author_reviews():
    if current_user.role != 'author':
        abort(403)
    # Get all books by this author
    author_books = Book.query.filter_by(author_id=current_user.id).all()
    book_ids = [b.id for b in author_books]
    # Get all reviews for these books
    reviews = Review.query.filter(Review.book_id.in_(book_ids)).order_by(Review.created_at.desc()).all() if book_ids else []
    return render_template('dashboard/author_reviews.html', reviews=reviews)


@app.route('/author/profile', methods=['GET', 'POST'])
@login_required
def author_profile():
    if current_user.role != 'author':
        abort(403)
    user = current_user
    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.username = request.form.get('pen_name')
        user.bio = request.form.get('bio')
        user.linkedin = request.form.get('linkedin')
        user.website = request.form.get('website')
        user.instagram = request.form.get('instagram')
        # Handle profile image upload
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.root_path, 'static/uploads', filename))
                user.profile_image = filename
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('author_profile'))
    return render_template('dashboard/author_profile.html', user=user)


@app.route('/become_author', methods=['POST'])
@login_required
def become_author():
    if current_user.role == 'author':
        flash('You are already an author!', 'info')
        return redirect(url_for('profile'))
    bio = request.form.get('bio')
    awards = request.form.get('awards')
    current_user.role = 'author'
    current_user.bio = bio
    current_user.awards = awards
    db.session.commit()
    flash('Congratulations! You are now an author. You can now access the Author Dashboard.', 'success')
    return redirect(url_for('author_dashboard'))


@app.route('/admin/users/role/<int:user_id>', methods=['POST'])
@login_required
def change_user_role(user_id):
    if current_user.role != 'publisher':
        abort(403)
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['author', 'student', 'vendor', 'publisher']:
        user.role = new_role
        db.session.commit()
        flash(f"User {user.username}'s role updated to {new_role}.", 'success')
    else:
        flash('Invalid role selected.', 'danger')
    return redirect(url_for('manage_users'))


@app.route('/author/delete_book/<int:book_id>', methods=['POST'])
@login_required
def delete_author_book(book_id):
    book = Book.query.get_or_404(book_id)
    if current_user.role != 'author' or book.author_id != current_user.id:
        abort(403)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully.', 'success')
    return redirect(url_for('author_books'))


@app.route('/author/reply_review/<int:review_id>', methods=['POST'])
@login_required
def reply_review(review_id):
    review = Review.query.get_or_404(review_id)
    book = Book.query.get(review.book_id)
    if not book or book.author_id != current_user.id:
        abort(403)
    reply_text = request.form.get('reply', '').strip()
    if reply_text:
        review.reply = reply_text
        db.session.commit()
        flash('Reply submitted successfully.', 'success')
    else:
        flash('Reply cannot be empty.', 'danger')
    return redirect(url_for('author_reviews'))


@app.route('/author/analytics')
@login_required
def author_analytics_dashboard():
    if current_user.role != 'author':
        abort(403)
    # Get all books by this author
    books = Book.query.filter_by(author_id=current_user.id).all()
    # Calculate sales count for each book
    for book in books:
        book.sales_count = sum([oi.quantity for oi in book.order_items]) if book.order_items else 0
    # Review trends: reviews per month for the last 6 months
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    review_trends = {'labels': [], 'data': []}
    avg_ratings = {'labels': [], 'data': []}
    for i in range(5, -1, -1):
        month = (now - timedelta(days=30*i)).strftime('%b %Y')
        review_trends['labels'].append(month)
        month_start = (now - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i == 0:
            month_end = now
        else:
            month_end = (now - timedelta(days=30*(i-1))).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_reviews = Review.query.join(Book).filter(
            Book.author_id == current_user.id,
            Review.created_at >= month_start,
            Review.created_at < month_end
        ).all()
        review_trends['data'].append(len(month_reviews))
        # Average rating for this month
        if month_reviews:
            avg_rating = round(sum([r.rating for r in month_reviews]) / len(month_reviews), 2)
        else:
            avg_rating = 0
        avg_ratings['labels'].append(month)
        avg_ratings['data'].append(avg_rating)
    return render_template('dashboard/author_analytics.html', books=books, review_trends=review_trends, avg_ratings=avg_ratings)


@app.route('/notifications/sample')  
@login_required       
def create_sample_notifications():
    from models import Notification, User 
    import random
    sample_messages = [
        ('Order Update', 'Your order #12345 has been shipped!', 'order'),
        ('Review Alert', 'A new review was posted for your book.', 'review'),
        ('System Info', 'Your profile was updated successfully.', 'system'),
        ('Royalty Update', 'Your royalty payment for March has been processed.', 'system'),
        ('Book Approved', 'Your new book has been approved and is now live!', 'system'),
        ('Flagged Review', 'A review for your book was flagged for moderation.', 'review'),
        ('Book Out of Stock', 'One of your books is out of stock.', 'system'),
        ('Order Cancelled', 'Order #12345 was cancelled by the user.', 'order'),
        ('Book Status Changed', 'Your book status was updated to "Published".', 'system'),
        ('Admin Alert', 'A new admin announcement is available.', 'system'),
    ]
    # If admin, create for all roles
    if current_user.role == 'publisher':
        users = User.query.all()
        for user in users:
            for title, message, ntype in sample_messages:
                notif = Notification(user_id=user.id, title=title, message=message, notification_type=ntype)
                db.session.add(notif)
    else:
        for title, message, ntype in sample_messages:
            notif = Notification(user_id=current_user.id, title=title, message=message, notification_type=ntype)
            db.session.add(notif)
    db.session.commit()
    flash('Sample notifications created for your account!', 'success')
    return redirect(url_for('notifications'))


@app.route('/create_razorpay_order', methods=['POST'])
@login_required
def create_razorpay_order():
    data = request.json
    order_id = data['order_id']
    amount = int(float(data['amount']) * 100)  # Convert to paise
    razorpay_order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })
    return jsonify({
        "razorpay_order_id": razorpay_order['id'],
        "razorpay_key": "YOUR_RAZORPAY_KEY_ID",
        "amount": amount
    })

@app.route('/verify_razorpay_payment', methods=['POST'])
@login_required
def verify_razorpay_payment():
    data = request.json
    order = Order.query.get(data['order_id'])
    params_dict = {
        'razorpay_order_id': data['razorpay_order_id'],
        'razorpay_payment_id': data['razorpay_payment_id'],
        'razorpay_signature': data['razorpay_signature']
    }
    try:
        # Verify payment signature
        razorpay_client.utility.verify_payment_signature(params_dict)
        # Update order status
        order.payment_status = 'paid'
        order.transaction_id = data['razorpay_payment_id']
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'success': False})
