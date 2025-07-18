from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, PasswordField, SubmitField, BooleanField, SelectMultipleField, DateTimeField, FileField as WTFileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, Optional, Regexp


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[
        ('student', 'Student/Buyer'),
        ('author', 'Author'),
        ('vendor', 'Vendor/Distributor'),
        ('publisher', 'Publisher')
    ], validators=[DataRequired()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    submit = SubmitField('Register')


class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=200)])
    isbn = StringField('ISBN', validators=[Optional(), Length(max=17), Regexp(r'^(97(8|9))?\d{9}(\d|X)$', message='Invalid ISBN format')])
    description = TextAreaField('Description', validators=[Optional()])
    category = SelectMultipleField('Category/Genre', choices=[], validators=[Optional()])
    tags = StringField('Tags/Keywords', validators=[Optional(), Length(max=200)])
    language = StringField('Language', validators=[Optional(), Length(max=50)])
    edition = StringField('Edition', validators=[Optional(), Length(max=50)])
    pages = IntegerField('Pages', validators=[Optional(), NumberRange(min=1)])
    est_reading_time = StringField('Estimated Reading Time', render_kw={'readonly': True})
    cover_image = FileField('Cover Image', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    manuscript_file = WTFileField('Manuscript File', validators=[Optional(), FileAllowed(['pdf', 'epub', 'docx'], 'PDF, ePub, DOCX only!')])
    sample_chapter = WTFileField('Sample Chapter', validators=[Optional(), FileAllowed(['pdf', 'epub', 'docx'], 'PDF, ePub, DOCX only!')])
    pen_name = StringField('Pen Name', validators=[Optional(), Length(max=100)])
    author_bio = TextAreaField('Short Author Bio', validators=[Optional(), Length(max=500)])
    co_authors = StringField('Co-author(s)', validators=[Optional(), Length(max=200)])
    price = FloatField('Regular Price', validators=[DataRequired(), NumberRange(min=0)])
    discount_price = FloatField('Discount Price', validators=[Optional(), NumberRange(min=0)])
    royalty_preference = SelectField('Royalty Preference', choices=[('fixed', 'Fixed %'), ('sliding', 'Sliding Scale'), ('custom', 'Custom')], validators=[Optional()])
    is_free = BooleanField('Is this book free?')
    visibility = SelectField('Visibility', choices=[('draft', 'Draft'), ('private', 'Private (link only)'), ('public', 'Public')], validators=[DataRequired()])
    schedule_publication = DateTimeField('Schedule Publication Date', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    allow_reviews = BooleanField('Allow Reader Reviews', default=True)
    early_access_reviews = BooleanField('Enable Early Access Reviews')
    featured = BooleanField('Featured Book')
    trailer_link = StringField('Book Trailer Link', validators=[Optional(), Length(max=200)])
    social_preview = StringField('Social Media Share Preview', validators=[Optional(), Length(max=200)])
    promo_badges = SelectMultipleField('Promotional Badges', choices=[('new', 'New Release'), ('bestseller', 'Bestseller'), ('award', 'Award-Winning')], validators=[Optional()])
    version_number = StringField('Version Number', validators=[Optional(), Length(max=20)])
    changelog = TextAreaField('Changelog', validators=[Optional(), Length(max=500)])
    save_as_draft = SubmitField('Save as Draft')
    submit_for_review = SubmitField('Submit for Review')
    preview = SubmitField('Preview Book Page')
    submit = SubmitField('Save Book')


class DocumentForm(FlaskForm):
    title = StringField('Document Title', validators=[DataRequired(), Length(min=1, max=200)])
    document_type = SelectField('Document Type', choices=[
        ('contract', 'Contract'),
        ('agreement', 'Agreement'),
        ('pan', 'PAN Card'),
        ('aadhaar', 'Aadhaar Card'),
        ('bank', 'Bank Details'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    file = FileField('Document File', validators=[DataRequired(), FileAllowed(['pdf', 'doc', 'docx', 'jpg', 'png'], 'Invalid file type!')])
    submit = SubmitField('Upload Document')


class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[
        ('5', '5 Stars'),
        ('4', '4 Stars'),
        ('3', '3 Stars'),
        ('2', '2 Stars'),
        ('1', '1 Star')
    ], validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Submit Review')


class RoyaltyForm(FlaskForm):
    percentage = FloatField('Royalty Percentage', validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Update Royalty')


class CheckoutForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=20)])
    address = TextAreaField('Shipping Address', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('razorpay', 'Razorpay'),
        ('paytm', 'Paytm'),
        ('cod', 'Cash on Delivery')
    ], validators=[DataRequired()])
    submit = SubmitField('Place Order')
