
from flask import render_template, request, redirect, url_for, flash, session, jsonify, abort, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_, func, desc
import pandas as pd
import os
import uuid
from datetime import datetime, timedelta
import json

from app import app, db
from models import User, Book, Order, OrderItem, Review, Royalty, Document, CartItem, Wishlist, Notification, Category, Analytics, ReviewHelpful
from forms import LoginForm, RegisterForm, BookForm, DocumentForm, ReviewForm, RoyaltyForm, CheckoutForm
from utils import allowed_file, generate_order_number, calculate_royalty


# Analytics and tracking
def track_event(event_type, book_id=None, search_query=None):
    """Track user events for analytics"""
    analytics = Analytics(
        event_type=event_type,
        user_id=current_user.id if current_user.is_authenticated else None,
        book_id=book_id,
        search_query=search_query,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(analytics)
    db.session.commit()


def create_notification(user_id, title, message, notification_type='system', order_id=None, book_id=None):
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        order_id=order_id,
        book_id=book_id
    )
    db.session.add(notification)
    db.session.commit()


# Advanced Analytics Dashboard
@app.route('/admin/analytics')
@login_required
def analytics_dashboard():
    if current_user.role != 'publisher':
        abort(403)
    
    # Get date range
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Page views
    page_views = Analytics.query.filter(
        Analytics.event_type == 'page_view',
        Analytics.created_at >= start_date
    ).count()
    
    # Book views
    book_views = Analytics.query.filter(
        Analytics.event_type == 'book_view',
        Analytics.created_at >= start_date
    ).count()
    
    # Popular books
    popular_books = db.session.query(
        Book.title, func.count(Analytics.id).label('views')
    ).join(Analytics).filter(
        Analytics.event_type == 'book_view',
        Analytics.created_at >= start_date
    ).group_by(Book.id).order_by(desc('views')).limit(10).all()
    
    # Popular searches
    popular_searches = db.session.query(
        Analytics.search_query, func.count(Analytics.id).label('count')
    ).filter(
        Analytics.event_type == 'search',
        Analytics.search_query.isnot(None),
        Analytics.created_at >= start_date
    ).group_by(Analytics.search_query).order_by(desc('count')).limit(10).all()
    
    # Sales data
    recent_orders = Order.query.filter(
        Order.created_at >= start_date
    ).count()
    
    total_revenue = db.session.query(func.sum(Order.total_amount)).filter(
        Order.payment_status == 'paid',
        Order.created_at >= start_date
    ).scalar() or 0
    
    # Daily sales chart data
    daily_sales_query = db.session.query(
        func.date(Order.created_at).label('date'),
        func.count(Order.id).label('orders'),
        func.sum(Order.total_amount).label('revenue')
    ).filter(
        Order.created_at >= start_date
    ).group_by(func.date(Order.created_at)).all()
    
    # Convert to serializable format
    daily_sales = [
        {
            'date': str(row.date) if row.date else None,
            'orders': row.orders,
            'revenue': float(row.revenue) if row.revenue else 0
        }
        for row in daily_sales_query
    ]
    
    return render_template('admin/analytics.html',
                         page_views=page_views,
                         book_views=book_views,
                         popular_books=popular_books,
                         popular_searches=popular_searches,
                         recent_orders=recent_orders,
                         total_revenue=total_revenue,
                         daily_sales=daily_sales,
                         days=days)


# Bulk Book Upload
@app.route('/admin/bulk_upload', methods=['GET', 'POST'])
@login_required
def bulk_upload_books():
    if current_user.role != 'publisher':
        abort(403)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith(('.xlsx', '.csv')):
            try:
                # Read the Excel/CSV file
                if file.filename.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    df = pd.read_csv(file)
                
                success_count = 0
                error_count = 0
                errors = []
                
                for index, row in df.iterrows():
                    try:
                        # Check if book already exists
                        existing_book = Book.query.filter_by(isbn=row.get('ISBN')).first()
                        if existing_book:
                            continue
                        
                        # Get or create author
                        author = None
                        if pd.notna(row.get('Author')):
                            author = User.query.filter_by(full_name=row['Author'], role='author').first()
                        
                        # Create book
                        book = Book(
                            title=row['Title'],
                            isbn=row.get('ISBN'),
                            description=row.get('Description', ''),
                            price=float(row['Price']),
                            wholesale_price=float(row.get('Wholesale_Price', row['Price'] * 0.8)),
                            stock=int(row.get('Stock', 0)),
                            pages=int(row.get('Pages', 0)) if pd.notna(row.get('Pages')) else None,
                            edition=row.get('Edition'),
                            publisher_name=row.get('Publisher'),
                            subject=row.get('Subject'),
                            exam_type=row.get('Exam_Type'),
                            language=row.get('Language', 'English'),
                            category=row.get('Category'),
                            keywords=row.get('Keywords'),
                            author_id=author.id if author else None,
                            publisher_id=current_user.id
                        )
                        
                        db.session.add(book)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row {index + 1}: {str(e)}")
                
                db.session.commit()
                
                flash(f'Bulk upload completed! {success_count} books added, {error_count} errors.', 'success')
                if errors:
                    flash('Errors: ' + '; '.join(errors[:5]), 'warning')
                
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
        
        else:
            flash('Please upload a valid Excel (.xlsx) or CSV file', 'error')
    
    return render_template('admin/bulk_upload.html')


# Notifications
@app.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=notifications)


@app.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        abort(403)
    notification.is_read = True
    db.session.commit()
    flash('Notification marked as read.', 'success')
    return redirect(url_for('notifications'))


@app.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications'))


# Advanced Search with Analytics
@app.route('/search')
def advanced_search():
    query = request.args.get('q', '')
    if query:
        track_event('search', search_query=query)
    
    # Advanced search parameters
    category_id = request.args.get('category', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_rating = request.args.get('min_rating', type=float)
    language = request.args.get('language')
    exam_type = request.args.get('exam_type')
    in_stock = request.args.get('in_stock', type=bool)
    
    # Build query
    search_query = Book.query.filter(Book.is_active == True)
    
    if query:
        search_query = search_query.filter(or_(
            Book.title.ilike(f'%{query}%'),
            Book.description.ilike(f'%{query}%'),
            Book.subject.ilike(f'%{query}%'),
            Book.keywords.ilike(f'%{query}%')
        ))
    
    # Fix: Use category name instead of category_id for filtering
    if category_id:
        category = Category.query.get(category_id)
        if category:
            search_query = search_query.filter(Book.category == category.name)
    
    if min_price:
        search_query = search_query.filter(Book.price >= min_price)
    
    if max_price:
        search_query = search_query.filter(Book.price <= max_price)
    
    if language:
        search_query = search_query.filter(Book.language == language)
    
    if exam_type:
        search_query = search_query.filter(Book.exam_type == exam_type)
    
    if in_stock:
        search_query = search_query.filter(Book.stock > 0)
    
    # Sorting
    sort_by = request.args.get('sort', 'relevance')
    if sort_by == 'price_low':
        search_query = search_query.order_by(Book.price.asc())
    elif sort_by == 'price_high':
        search_query = search_query.order_by(Book.price.desc())
    elif sort_by == 'newest':
        search_query = search_query.order_by(Book.created_at.desc())
    elif sort_by == 'popular':
        search_query = search_query.order_by(Book.view_count.desc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    books = search_query.paginate(page=page, per_page=12, error_out=False)
    
    # Get filter options
    categories = Category.query.filter_by(is_active=True).all()
    languages = db.session.query(Book.language).distinct().all()
    exam_types = db.session.query(Book.exam_type).distinct().all()
    
    return render_template('advanced_search.html',
                         books=books,
                         query=query,
                         categories=categories,
                         languages=[l[0] for l in languages if l[0]],
                         exam_types=[e[0] for e in exam_types if e[0]],
                         **request.args)


# Category Management
@app.route('/admin/categories')
@login_required
def manage_categories():
    if current_user.role != 'publisher':
        abort(403)
    
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)


@app.route('/admin/categories/add', methods=['POST'])
@login_required
def add_category():
    if current_user.role != 'publisher':
        abort(403)
    
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    if name:
        category = Category(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
    
    return redirect(url_for('manage_categories'))


@app.route('/admin/categories/delete/<int:category_id>')
@login_required
def delete_category(category_id):
    if current_user.role != 'publisher':
        abort(403)
    
    category = Category.query.get_or_404(category_id)
    category.is_active = False
    db.session.commit()
    flash('Category deactivated successfully!', 'success')
    
    return redirect(url_for('manage_categories'))


# Review Moderation
@app.route('/admin/reviews')
@login_required
def moderate_reviews():
    if current_user.role != 'publisher':
        abort(403)
    # Show all reviews for moderation
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/moderate_reviews.html', reviews=reviews)

@app.route('/admin/reviews/approve/<int:review_id>')
@login_required
def approve_review(review_id):
    if current_user.role != 'publisher':
        abort(403)
    review = Review.query.get_or_404(review_id)
    review.is_approved = True
    review.is_flagged = False
    db.session.commit()
    flash('Review approved!', 'success')
    return redirect(url_for('moderate_reviews'))

@app.route('/admin/reviews/reject/<int:review_id>')
@login_required
def reject_review(review_id):
    if current_user.role != 'publisher':
        abort(403)
    review = Review.query.get_or_404(review_id)
    review.is_approved = False
    review.is_flagged = True
    db.session.commit()
    flash('Review rejected and flagged!', 'warning')
    return redirect(url_for('moderate_reviews'))

@app.route('/admin/reviews/edit/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    if current_user.role != 'publisher':
        abort(403)
    review = Review.query.get_or_404(review_id)
    if request.method == 'POST':
        review.comment = request.form.get('comment', review.comment)
        review.rating = int(request.form.get('rating', review.rating))
        db.session.commit()
        flash('Review updated!', 'success')
        return redirect(url_for('moderate_reviews'))
    return render_template('admin/edit_review.html', review=review)

@app.route('/admin/reviews/delete/<int:review_id>')
@login_required
def delete_review(review_id):
    if current_user.role != 'publisher':
        abort(403)
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash('Review deleted!', 'success')
    return redirect(url_for('moderate_reviews'))

# --- Auto-flagging on review submission ---
def contains_inappropriate_language(text):
    bad_words = ['spam', 'scam', 'fake', 'badword1', 'badword2']
    text_lower = text.lower()
    return any(word in text_lower for word in bad_words)

@app.route('/review_book/<int:book_id>', methods=['POST'])
@login_required
def review_book(book_id):
    form = ReviewForm()
    if form.validate_on_submit():
        # Check if user already reviewed this book
        existing_review = Review.query.filter_by(user_id=current_user.id, book_id=book_id).first()
        if existing_review:
            flash('You have already reviewed this book', 'warning')
            return redirect(url_for('book_detail', book_id=book_id))
        comment = form.comment.data
        is_flagged = contains_inappropriate_language(comment)
        review = Review(
            user_id=current_user.id,
            book_id=book_id,
            rating=int(form.rating.data),
            comment=comment,
            is_approved=not is_flagged,  # Only auto-approve if not flagged
            is_flagged=is_flagged
        )
        db.session.add(review)
        db.session.commit()
        # Notify the author
        book = Book.query.get(book_id)
        if book and book.author_id:
            author = User.query.get(book.author_id)
            if author:
                notification = Notification(
                    user_id=author.id,
                    title=f'New Review for "{book.title}"',
                    message=f'{current_user.full_name} rated {review.rating}/5: "{(review.comment[:100] + "...") if review.comment and len(review.comment) > 100 else review.comment}"',
                    notification_type='review',
                    book_id=book.id
                )
                db.session.add(notification)
                db.session.commit()
                # Emit real-time notification to the author
                socketio.emit('new_review_notification', {
                    'user_id': author.id,
                    'title': notification.title,
                    'message': notification.message,
                    'book_id': book.id,
                    'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M')
                }, namespace='/notifications', broadcast=True)
        if is_flagged:
            flash('Your review contains inappropriate content and is pending moderation.', 'warning')
        else:
            flash('Review submitted successfully!', 'success')
    return redirect(url_for('book_detail', book_id=book_id))

# Only approved reviews are public (already enforced in book detail route)


# Flag review
@app.route('/flag_review/<int:review_id>')
@login_required
def flag_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.is_flagged = True
    db.session.commit()
    
    flash('Review flagged for moderation', 'info')
    return redirect(url_for('book_detail', book_id=review.book_id))


# User Management (Admin)
@app.route('/admin/users')
@login_required
def manage_users():
    if current_user.role != 'publisher':
        abort(403)
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/ban/<int:user_id>')
@login_required
def ban_user(user_id):
    if current_user.role != 'publisher':
        abort(403)
    
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    
    flash(f'User {user.username} has been banned', 'success')
    return redirect(url_for('manage_users'))


@app.route('/admin/users/unban/<int:user_id>')
@login_required
def unban_user(user_id):
    if current_user.role != 'publisher':
        abort(403)
    
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    
    flash(f'User {user.username} has been unbanned', 'success')
    return redirect(url_for('manage_users'))


# Enhanced Book Details with Analytics Tracking
@app.route('/book/<int:book_id>')
def enhanced_book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    
    # Track book view
    track_event('book_view', book_id=book_id)
    
    # Increment view count
    if book.view_count is None:
        book.view_count = 0
    book.view_count += 1
    db.session.commit()
    
    # Get approved reviews with helpful votes (handle missing column gracefully)
    try:
        reviews = Review.query.filter_by(
            book_id=book_id, 
            is_approved=True
        ).order_by(
            Review.helpful_votes.desc(), 
            Review.created_at.desc()
        ).all()
    except Exception as e:
        # Fallback if helpful_votes column doesn't exist yet
        reviews = Review.query.filter_by(
            book_id=book_id, 
            is_approved=True
        ).order_by(
            Review.created_at.desc()
        ).all()
    
    # Get recommended books using advanced algorithm
    recommended_books = get_advanced_recommendations(book_id)
    
    # Check if current user has this book in wishlist
    in_wishlist = False
    user_review = None
    if current_user.is_authenticated:
        in_wishlist = Wishlist.query.filter_by(user_id=current_user.id, book_id=book_id).first() is not None
        user_review = Review.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    
    return render_template('enhanced_book_detail.html', 
                         book=book, 
                         reviews=reviews, 
                         recommended_books=recommended_books,
                         in_wishlist=in_wishlist,
                         user_review=user_review)


def get_advanced_recommendations(book_id, limit=6):
    """Advanced recommendation algorithm"""
    current_book = Book.query.get(book_id)
    if not current_book:
        return []
    
    recommendations = []
    seen_ids = {book_id}
    
    # 1. Books by same author (weight: 3)
    if current_book.author_id:
        author_books = Book.query.filter(
            Book.author_id == current_book.author_id,
            Book.id != book_id,
            Book.is_active == True
        ).order_by(Book.view_count.desc()).limit(3).all()
        recommendations.extend(author_books)
        seen_ids.update(book.id for book in author_books)
    
    # 2. Books in same category and exam type (weight: 2)
    if current_book.category and current_book.exam_type:
        category_books = Book.query.filter(
            Book.category == current_book.category,
            Book.exam_type == current_book.exam_type,
            Book.id.notin_(seen_ids),
            Book.is_active == True
        ).order_by(Book.view_count.desc()).limit(2).all()
        recommendations.extend(category_books)
        seen_ids.update(book.id for book in category_books)
    
    # 3. Books with similar keywords (weight: 1)
    if current_book.keywords:
        keywords = [k.strip().lower() for k in current_book.keywords.split(',')]
        for keyword in keywords[:3]:
            keyword_books = Book.query.filter(
                Book.keywords.ilike(f'%{keyword}%'),
                Book.id.notin_(seen_ids),
                Book.is_active == True
            ).limit(1).all()
            recommendations.extend(keyword_books)
            seen_ids.update(book.id for book in keyword_books)
    
    # 4. Fill remaining with popular books in same price range
    if len(recommendations) < limit:
        price_range_books = Book.query.filter(
            Book.price.between(current_book.price * 0.7, current_book.price * 1.3),
            Book.id.notin_(seen_ids),
            Book.is_active == True
        ).order_by(Book.view_count.desc()).limit(limit - len(recommendations)).all()
        recommendations.extend(price_range_books)
    
    return recommendations[:limit]


# Export data
@app.route('/admin/export/<data_type>')
@login_required
def export_data(data_type):
    if current_user.role != 'publisher':
        abort(403)
    
    export_format = request.args.get('format', 'xlsx')
    if data_type == 'books':
        books = Book.query.all()
        data = [{
            'ID': book.id,
            'Title': book.title,
            'Author': book.author.full_name if book.author else '',
            'Price': book.price,
            'Stock': book.stock,
            'Category': book.category,
            'Exam Type': book.exam_type,
            'Created': book.created_at.strftime('%Y-%m-%d')
        } for book in books]
        
    elif data_type == 'orders':
        orders = Order.query.all()
        data = [{
            'Order Number': order.order_number,
            'User': order.user.full_name,
            'Total': order.total_amount,
            'Status': order.status,
            'Payment Status': order.payment_status,
            'Created': order.created_at.strftime('%Y-%m-%d')
        } for order in orders]
        
    elif data_type == 'users':
        users = User.query.all()
        data = [{
            'ID': user.id,
            'Username': user.username,
            'Email': user.email,
            'Full Name': user.full_name,
            'Role': user.role,
            'Active': user.is_active,
            'Created': user.created_at.strftime('%Y-%m-%d')
        } for user in users]
    
    else:
        abort(404)
    
    # Create DataFrame and export to Excel or CSV
    import pandas as pd
    from datetime import datetime
    import os
    df = pd.DataFrame(data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if export_format == 'csv':
        filename = f'{data_type}_export_{timestamp}.csv'
        filepath = os.path.join('/tmp', filename)
        df.to_csv(filepath, index=False)
        mimetype = 'text/csv'
    else:
        # Before saving the Excel file, ensure the export directory exists
        EXPORT_DIR = os.path.join(os.getcwd(), 'static', 'exports')
        os.makedirs(EXPORT_DIR, exist_ok=True)
        filepath = os.path.join(EXPORT_DIR, 'export.xlsx')
        df.to_excel(filepath, index=False)
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype=mimetype)


# Edit Book Route
@app.route('/admin/books/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    if current_user.role != 'publisher':
        abort(403)
    
    book = Book.query.get_or_404(book_id)
    # Get all authors for dropdown
    from models import User
    authors = User.query.filter_by(role='author', is_active=True).all()
    
    if request.method == 'POST':
        try:
            def safe_float(val, default=0.0):
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return default
            def safe_int(val, default=0):
                try:
                    return int(val)
                except (TypeError, ValueError):
                    return default

            book.title = request.form.get('title')
            book.isbn = request.form.get('isbn')
            book.description = request.form.get('description')
            book.price = safe_float(request.form.get('price'))
            book.wholesale_price = safe_float(request.form.get('wholesale_price'))
            book.stock = safe_int(request.form.get('stock'))
            book.pages = safe_int(request.form.get('pages')) if request.form.get('pages') else None
            book.edition = request.form.get('edition')
            book.publisher_name = request.form.get('publisher_name')
            book.subject = request.form.get('subject')
            book.exam_type = request.form.get('exam_type')
            book.language = request.form.get('language', 'English')
            book.category = request.form.get('category')
            book.keywords = request.form.get('keywords')

            # Save author_name and auto-link author_id
            author_select = request.form.get('author_name', '').strip()
            new_author_name = request.form.get('new_author_name', '').strip()
            new_author_email = request.form.get('new_author_email', '').strip()
            if author_select == '__new__' and new_author_name:
                author_name = new_author_name
            else:
                author_name = author_select
            book.author_name = author_name
            author_user = User.query.filter_by(full_name=author_name, role='author').first()
            if not author_user and author_name:
                # Require email for new author
                if not new_author_email:
                    flash('Email is required for new authors.', 'error')
                    db.session.rollback()
                    return render_template('dashboard/edit_book.html', book=book, authors=authors)
                author_user = User(full_name=author_name, role='author', is_active=True, username=author_name.lower().replace(' ', '_'), email=new_author_email)
                db.session.add(author_user)
                db.session.commit()
            if author_user:
                book.author_id = author_user.id
            else:
                book.author_id = None
            db.session.commit()
            flash('Book updated successfully!', 'success')
            return redirect(url_for('manage_books'))
        except Exception as e:
            flash(f'Error updating book: {str(e)}', 'error')
    return render_template('dashboard/edit_book.html', book=book, authors=authors)


# Delete Book Route
@app.route('/admin/books/delete/<int:book_id>')
@login_required
def delete_book(book_id):
    if current_user.role != 'publisher':
        abort(403)
    
    book = Book.query.get_or_404(book_id)
    
    try:
        # Soft delete - just mark as inactive
        book.is_active = False
        db.session.commit()
        flash('Book deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting book: {str(e)}', 'error')
    
    return redirect(url_for('manage_books'))


# Track page views for analytics
@app.before_request
def track_page_views():
    if request.endpoint and not request.endpoint.startswith('static'):
        track_event('page_view')


@app.route('/admin/popular_searches_data')
@login_required
def popular_searches_data():
    if current_user.role != 'publisher':
        abort(403)
    # Get date range from query params
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else datetime.utcnow() - timedelta(days=30)
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else datetime.utcnow()
    except Exception:
        return jsonify({'error': 'Invalid date format'}), 400

    # Get previous period for trend calculation
    period_days = (end_date - start_date).days or 1
    prev_start = start_date - timedelta(days=period_days)
    prev_end = start_date

    # Current period popular searches
    current_searches = dict(db.session.query(
        Analytics.search_query, func.count(Analytics.id)
    ).filter(
        Analytics.event_type == 'search',
        Analytics.search_query.isnot(None),
        Analytics.created_at >= start_date,
        Analytics.created_at <= end_date
    ).group_by(Analytics.search_query).all())

    # Previous period popular searches
    prev_searches = dict(db.session.query(
        Analytics.search_query, func.count(Analytics.id)
    ).filter(
        Analytics.event_type == 'search',
        Analytics.search_query.isnot(None),
        Analytics.created_at >= prev_start,
        Analytics.created_at < prev_end
    ).group_by(Analytics.search_query).all())

    # Build result with trend
    result = []
    for search, count in sorted(current_searches.items(), key=lambda x: x[1], reverse=True):
        prev_count = prev_searches.get(search, 0)
        if count > prev_count:
            trend = 'up'
        elif count < prev_count:
            trend = 'down'
        else:
            trend = 'same'
        result.append({'search': search, 'count': count, 'trend': trend})
    return jsonify(result)

@app.route('/admin/reviews/bulk_approve', methods=['POST'])
@login_required
def bulk_approve_reviews():
    if current_user.role != 'publisher':
        abort(403)
    ids = request.json.get('review_ids', [])
    for rid in ids:
        review = Review.query.get(rid)
        if review:
            review.is_approved = True
            review.is_flagged = False
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/reviews/bulk_reject', methods=['POST'])
@login_required
def bulk_reject_reviews():
    if current_user.role != 'publisher':
        abort(403)
    ids = request.json.get('review_ids', [])
    for rid in ids:
        review = Review.query.get(rid)
        if review:
            review.is_approved = False
            review.is_flagged = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/reviews/bulk_delete', methods=['POST'])
@login_required
def bulk_delete_reviews():
    if current_user.role != 'publisher':
        abort(403)
    ids = request.json.get('review_ids', [])
    for rid in ids:
        review = Review.query.get(rid)
        if review:
            db.session.delete(review)
    db.session.commit()
    return jsonify({'success': True})
