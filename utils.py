import os
import uuid
from datetime import datetime
from app import db
from models import Royalty


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_order_number():
    """Generate a unique order number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = str(uuid.uuid4())[:8].upper()
    return f"ORD-{timestamp}-{random_part}"


def calculate_royalty(book_id, quantity, price):
    """Calculate and update royalty for a book sale"""
    royalty_record = Royalty.query.filter_by(book_id=book_id).first()
    if royalty_record:
        royalty_amount = (price * quantity * royalty_record.percentage) / 100
        royalty_record.sales_count += quantity
        royalty_record.total_earnings += royalty_amount
        db.session.commit()
