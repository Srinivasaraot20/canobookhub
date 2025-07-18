
from app import app, db
from models import User, Book
from werkzeug.security import generate_password_hash

def populate_sample_data():
    with app.app_context():
        # Create sample authors if they don't exist
        authors = [
            {"username": "rknarayan", "email": "rk@example.com", "full_name": "R.K. Narayan", 
             "bio": "Rasipuram Krishnaswami Iyer Narayanaswami was an Indian writer known for his works set in the fictional South Indian town of Malgudi.", 
             "awards": "Sahitya Akademi Award, Padma Bhushan, Padma Vibhushan"},
            {"username": "apjkalam", "email": "kalam@example.com", "full_name": "A.P.J. Abdul Kalam", 
             "bio": "Avul Pakir Jainulabdeen Abdul Kalam was an Indian aerospace scientist and politician who served as the 11th President of India.", 
             "awards": "Bharat Ratna, Padma Vibhushan, Padma Bhushan"},
            {"username": "chavla", "email": "chavla@example.com", "full_name": "Chetan Bhagat", 
             "bio": "Chetan Bhagat is an Indian author, columnist, screenwriter, television personality and motivational speaker.", 
             "awards": "Society Young Achievers Award"},
            {"username": "aroyauthor", "email": "aroy@example.com", "full_name": "Arundhati Roy", 
             "bio": "Suzanna Arundhati Roy is an Indian author best known for her novel The God of Small Things.", 
             "awards": "Booker Prize, Sahitya Akademi Award"},
            {"username": "vsgaikar", "email": "gaikar@example.com", "full_name": "V.S. Gaitonde", 
             "bio": "Expert in competitive exam preparation with over 20 years of experience.", 
             "awards": "Best Teacher Award 2020"},
        ]
        
        for author_data in authors:
            if not User.query.filter_by(username=author_data["username"]).first():
                author = User(
                    username=author_data["username"],
                    email=author_data["email"],
                    password_hash=generate_password_hash("password123"),
                    full_name=author_data["full_name"],
                    role="author",
                    bio=author_data["bio"],
                    awards=author_data["awards"]
                )
                db.session.add(author)
        
        db.session.commit()
        
        # Get authors
        authors_dict = {author.username: author for author in User.query.filter_by(role="author").all()}
        
        # Sample books data
        books_data = [
            # Literature & Fiction
            {
                "title": "srinu",
                "isbn": "9780140185577",
                "description": "A collection of short stories set in the fictional town of Malgudi, showcasing the everyday lives of ordinary people.",
                "price": 299.0,
                "stock": 50,
                "pages": 256,
                "edition": "1st",
                "publisher_name": "Penguin Classics",
                "subject": "Literature",    
                "exam_type": "General",
                "language": "English",
                "category": "Fiction",
                "keywords": "indian literature, short stories, malgudi, classic",
                "author_username": "rknarayan"
            },
            {
                "title": "The Guide",
                "isbn": "9780140183542",
                "description": "The story of Raju, a tour guide who becomes a spiritual guide and eventually a revered holy man.",
                "price": 350.0,
                "stock": 35,
                "pages": 220,
                "edition": "2nd",
                "publisher_name": "Penguin Classics",
                "subject": "Literature",
                "exam_type": "General",
                "language": "English",
                "category": "Fiction",
                "keywords": "indian literature, sahitya akademi, classic novel",
                "author_username": "rknarayan"
            },
            
            # Motivational & Biography
            {
                "title": "Wings of Fire",
                "isbn": "9788173711466",
                "description": "An autobiography of A.P.J. Abdul Kalam, covering his early life, his career as a scientist, and his vision for India.",
                "price": 199.0,
                "stock": 100,
                "pages": 180,
                "edition": "3rd",
                "publisher_name": "Universities Press",
                "subject": "Biography",
                "exam_type": "General",
                "language": "English",
                "category": "Non-fiction",
                "keywords": "autobiography, scientist, president, motivation, india",
                "author_username": "apjkalam"
            },
            {
                "title": "Ignited Minds",
                "isbn": "9780143400097",
                "description": "A book that seeks to inspire the youth of India to think creatively and become innovators.",
                "price": 250.0,
                "stock": 75,
                "pages": 200,
                "edition": "1st",
                "publisher_name": "Penguin Books",
                "subject": "Motivation",
                "exam_type": "General",
                "language": "English",
                "category": "Non-fiction",
                "keywords": "youth, innovation, creativity, motivation, development",
                "author_username": "apjkalam"
            },
            
            # Popular Fiction
            {
                "title": "Five Point Someone",
                "isbn": "9788129109545",
                "description": "A story about three friends and their adventures at the Indian Institute of Technology.",
                "price": 175.0,
                "stock": 80,
                "pages": 267,
                "edition": "1st",
                "publisher_name": "Rupa Publications",
                "subject": "Fiction",
                "exam_type": "General",
                "language": "English",
                "category": "Fiction",
                "keywords": "iit, friendship, college, youth, engineering",
                "author_username": "chavla"
            },
            {
                "title": "2 States",
                "isbn": "9788129115300",
                "description": "A love story about a couple from two different Indian states and their struggle to get married.",
                "price": 199.0,
                "stock": 60,
                "pages": 269,
                "edition": "1st",
                "publisher_name": "Rupa Publications",
                "subject": "Fiction",
                "exam_type": "General",
                "language": "English",
                "category": "Romance",
                "keywords": "love story, marriage, indian culture, comedy",
                "author_username": "chavla"
            },
            
            # Award-winning Literature
            {
                "title": "The God of Small Things",
                "isbn": "9780006550686",
                "description": "A semi-autobiographical novel that depicts the childhood experiences of fraternal twins.",
                "price": 450.0,
                "stock": 40,
                "pages": 340,
                "edition": "1st",
                "publisher_name": "HarperCollins",
                "subject": "Literature",
                "exam_type": "General",
                "language": "English",
                "category": "Fiction",
                "keywords": "booker prize, kerala, childhood, family, tragedy",
                "author_username": "aroyauthor"
            },
            
            # UPSC Preparation Books
            {
                "title": "Indian Polity by M. Laxmikanth",
                "isbn": "9789389645255",
                "description": "Comprehensive book on Indian Polity for UPSC Civil Services Examination.",
                "price": 750.0,
                "stock": 120,
                "pages": 896,
                "edition": "6th",
                "publisher_name": "McGraw Hill Education",
                "subject": "Political Science",
                "exam_type": "UPSC",
                "language": "English",
                "category": "Academic",
                "keywords": "upsc, civil services, polity, constitution, government",
                "author_username": "vsgaikar"
            },
            {
                "title": "Indian Economy by Ramesh Singh",
                "isbn": "9789353943080",
                "description": "Comprehensive coverage of Indian Economy for competitive examinations.",
                "price": 650.0,
                "stock": 90,
                "pages": 1200,
                "edition": "12th",
                "publisher_name": "McGraw Hill Education",
                "subject": "Economics",
                "exam_type": "UPSC",
                "language": "English",
                "category": "Academic",
                "keywords": "upsc, economics, indian economy, competitive exam",
                "author_username": "vsgaikar"
            },
            {
                "title": "Modern History of India",
                "isbn": "9789390122189",
                "description": "Complete coverage of Modern Indian History for UPSC and other competitive exams.",
                "price": 550.0,
                "stock": 85,
                "pages": 650,
                "edition": "4th",
                "publisher_name": "Orient BlackSwan",
                "subject": "History",
                "exam_type": "UPSC",
                "language": "English",
                "category": "Academic",
                "keywords": "upsc, modern history, india, british rule, freedom struggle",
                "author_username": "vsgaikar"
            },
            {
                "title": "Geography of India",
                "isbn": "9789355012234",
                "description": "Physical and Human Geography of India for competitive examinations.",
                "price": 495.0,
                "stock": 70,
                "pages": 480,
                "edition": "3rd",
                "publisher_name": "McGraw Hill Education",
                "subject": "Geography",
                "exam_type": "UPSC",
                "language": "English",
                "category": "Academic",
                "keywords": "upsc, geography, india, physical, human geography",
                "author_username": "vsgaikar"
            },
            
            # JEE Preparation Books
            {
                "title": "Concepts of Physics - Vol 1",
                "isbn": "9788177091878",
                "description": "Comprehensive Physics book for JEE Main and Advanced preparation.",
                "price": 475.0,
                "stock": 150,
                "pages": 462,
                "edition": "Revised",
                "publisher_name": "Bharati Bhawan",
                "subject": "Physics",
                "exam_type": "JEE",
                "language": "English",
                "category": "Academic",
                "keywords": "jee, physics, concepts, mechanics, waves",
                "author_username": "vsgaikar"
            },
            {
                "title": "Concepts of Physics - Vol 2",
                "isbn": "9788177091885",
                "description": "Advanced Physics concepts for JEE Main and Advanced.",
                "price": 475.0,
                "stock": 140,
                "pages": 518,
                "edition": "Revised",
                "publisher_name": "Bharati Bhawan",
                "subject": "Physics",
                "exam_type": "JEE",
                "language": "English",
                "category": "Academic",
                "keywords": "jee, physics, thermodynamics, optics, modern physics",
                "author_username": "vsgaikar"
            },
            {
                "title": "Mathematics for JEE - Algebra",
                "isbn": "9789389028485",
                "description": "Complete Algebra for JEE Main and Advanced with solved examples.",
                "price": 525.0,
                "stock": 125,
                "pages": 720,
                "edition": "2nd",
                "publisher_name": "Pearson Education",
                "subject": "Mathematics",
                "exam_type": "JEE",
                "language": "English",
                "category": "Academic",
                "keywords": "jee, mathematics, algebra, equations, functions",
                "author_username": "vsgaikar"
            },
            {
                "title": "Organic Chemistry for JEE",
                "isbn": "9789350949664",
                "description": "Comprehensive Organic Chemistry for JEE preparation with practice problems.",
                "price": 595.0,
                "stock": 110,
                "pages": 892,
                "edition": "3rd",
                "publisher_name": "McGraw Hill Education",
                "subject": "Chemistry",
                "exam_type": "JEE",
                "language": "English",
                "category": "Academic",
                "keywords": "jee, chemistry, organic, reactions, mechanisms",
                "author_username": "vsgaikar"
            },
            
            # NEET Preparation Books
            {
                "title": "Biology for NEET - Vol 1",
                "isbn": "9789389583457",
                "description": "Complete Biology coverage for NEET with diagrams and practice questions.",
                "price": 450.0,
                "stock": 95,
                "pages": 650,
                "edition": "5th",
                "publisher_name": "Arihant Publications",
                "subject": "Biology",
                "exam_type": "NEET",
                "language": "English",
                "category": "Academic",
                "keywords": "neet, biology, botany, zoology, medical entrance",
                "author_username": "vsgaikar"
            },
            {
                "title": "Biology for NEET - Vol 2",
                "isbn": "9789389583464",
                "description": "Advanced Biology concepts for NEET with latest syllabus coverage.",
                "price": 450.0,
                "stock": 90,
                "pages": 680,
                "edition": "5th",
                "publisher_name": "Arihant Publications",
                "subject": "Biology",
                "exam_type": "NEET",
                "language": "English",
                "category": "Academic",
                "keywords": "neet, biology, genetics, ecology, evolution",
                "author_username": "vsgaikar"
            },
            {
                "title": "Physics for NEET",
                "isbn": "9789389583471",
                "description": "Complete Physics for NEET examination with solved examples.",
                "price": 525.0,
                "stock": 105,
                "pages": 780,
                "edition": "4th",
                "publisher_name": "Arihant Publications",
                "subject": "Physics",
                "exam_type": "NEET",
                "language": "English",
                "category": "Academic",
                "keywords": "neet, physics, mechanics, electricity, magnetism",
                "author_username": "vsgaikar"
            },
            
            # SSC Preparation Books
            {
                "title": "SSC Mathematics",
                "isbn": "9789389583488",
                "description": "Complete Mathematics for SSC CGL, CHSL and other SSC examinations.",
                "price": 395.0,
                "stock": 80,
                "pages": 580,
                "edition": "6th",
                "publisher_name": "Kiran Prakashan",
                "subject": "Mathematics",
                "exam_type": "SSC",
                "language": "English",
                "category": "Academic",
                "keywords": "ssc, mathematics, arithmetic, algebra, geometry",
                "author_username": "vsgaikar"
            },
            {
                "title": "SSC English Language",
                "isbn": "9789389583495",
                "description": "Complete English Language preparation for SSC examinations.",
                "price": 325.0,
                "stock": 75,
                "pages": 420,
                "edition": "7th",
                "publisher_name": "Kiran Prakashan",
                "subject": "English",
                "exam_type": "SSC",
                "language": "English",
                "category": "Academic",
                "keywords": "ssc, english, grammar, vocabulary, comprehension",
                "author_username": "vsgaikar"
            },
            {
                "title": "SSC General Knowledge",
                "isbn": "9789389583502",
                "description": "Comprehensive General Knowledge for all SSC examinations.",
                "price": 425.0,
                "stock": 85,
                "pages": 720,
                "edition": "8th",
                "publisher_name": "Kiran Prakashan",
                "subject": "General Knowledge",
                "exam_type": "SSC",
                "language": "English",
                "category": "Academic",
                "keywords": "ssc, general knowledge, current affairs, history, geography",
                "author_username": "vsgaikar"
            },
            
            # Additional Popular Books
            {
                "title": "The Alchemist",
                "isbn": "9780061120084",
                "description": "A philosophical book about a young shepherd's journey to find treasure.",
                "price": 299.0,
                "stock": 65,
                "pages": 163,
                "edition": "25th Anniversary",
                "publisher_name": "HarperOne",
                "subject": "Philosophy",
                "exam_type": "General",
                "language": "English",
                "category": "Fiction",
                "keywords": "philosophy, journey, dreams, self-discovery",
                "author_username": "rknarayan"
            },
        ]  # End of books_data list

        # Update or add Think and Grow Rich with full details and correct cover image
        from models import Book
        with app.app_context():
            existing_tgr = Book.query.filter((Book.title.ilike('%think and grow rich%')) | (Book.isbn == '9788192910918')).first()
            tgr_data = {
                "title": "Think and Grow Rich",
                "isbn": "9788192910918",
                "description": "Think and Grow Rich has earned itself the reputation of being considered a textbook for actionable techniques that can help one get better at doing anything, not just by rich and wealthy, but also by people doing wonderful work in their respective fields. There are hundreds and thousands of successful people in the world who can vouch for the contents of this book. At the time of authors death, about 20 million copies had already been sold. Numerous revisions have been made in the book, from time to time, to make the book more readable and comprehensible to the readers. The book details out the most fundamental questions that once bothered the author, Napoleon Hill. The author once set out on a personal quest to find out what really made some people so successful. Why is it that some people manage to remain healthy, happy and financially independent, all at the same time? Why, after all, do some end up being called as lucky? The answers, no wonder, had to be no less than revelations. For more than a decade, the author interviewed some of the wealthiest and most successful people in the world. It was based on what author learnt in the process from all these people, when asked about how they achieved not just great riches but also personal wellbeing. The author formulated hundreds and thousands of answers, into concise principles which when acted upon, many claim, can help one achieve unprecedented success. The author has in many places narrated short stories and examples that help explain the concept at hand in an engaging manner. Think and Grow Rich teaches not just concepts but also methods. It is not a book that a reader can use for one time consumption. The book, even author recommends, has to be read one Chapter at a time and in sequence. Several readers and even some motivational speakers claim to have been reading this book over and over again, few pages at a time, for a long time now. Till date, it remains the number one self help book in the world, as far as sales are concerned! About author: an American journalist, lecturer and author, Napoleon Hill is one of the earliest producers of 'personal-success literature'. as an author of self-help books, Hill has always abided by and promoted principle of intense and burning passion being the sole key to achieve success. Hill has authored numerous books among which think and Grow Rich has been his most well-known works and had sold over 20 million copies back in the 1930s.",
                "price": 299.0,
                "stock": 100,
                "pages": 250,
                "edition": "2014 Paperback",
                "publisher_name": "Amazing Reads",
                "subject": "Business & Economics",
                "exam_type": "General",
                "language": "English",
                "category": "Personal Transformation",
                "keywords": "success, motivation, self-help, business, personal transformation",
                "cover_image": "https://m.media-amazon.com/images/I/71AdHA+qqwL._SL1500_.jpg",
                "amazon_link": "https://www.amazon.in/Think-Grow-Rich-Napoleon-Hill/dp/8192910911"
            }
            if existing_tgr:
                for k, v in tgr_data.items():
                    setattr(existing_tgr, k, v)
                db.session.commit()
            else:
                books_data.append(tgr_data)

        # Ensure unique cover images for each book
        used_images = set()
        for book in books_data:
            img = book.get('cover_image')
            if img:
                if img in used_images:
                    # If duplicate, append a unique suffix
                    import uuid
                    if '?' in img:
                        book['cover_image'] = img + f'&unique={uuid.uuid4().hex[:8]}'
                    else:
                        book['cover_image'] = img + f'?unique={uuid.uuid4().hex[:8]}'
                used_images.add(book['cover_image'])

        # Remove duplicates from books_data based on ISBN
        seen_isbns = set()
        unique_books_data = []
        for book in books_data:
            if book["isbn"] not in seen_isbns:
                unique_books_data.append(book)
                seen_isbns.add(book["isbn"])
        books_data = unique_books_data

        # Remove 'discount_price' from each book dict in books_data
        for book in books_data:
            if 'discount_price' in book:
                del book['discount_price']

        for book_data in books_data:
            # Check if book already exists
            existing_book = Book.query.filter_by(isbn=book_data["isbn"]).first()
            if existing_book:
                # Update fields as needed
                existing_book.title = book_data["title"]
                existing_book.description = book_data["description"]
                existing_book.price = book_data["price"]
                existing_book.stock = book_data["stock"]
                existing_book.pages = book_data["pages"]
                existing_book.edition = book_data["edition"]
                existing_book.publisher_name = book_data["publisher_name"]
                existing_book.subject = book_data["subject"]
                existing_book.exam_type = book_data["exam_type"]
                existing_book.language = book_data["language"]
                existing_book.category = book_data["category"]
                existing_book.keywords = book_data["keywords"]
                existing_book.author_id = authors_dict.get(book_data["author_username"]).id
                existing_book.cover_image = book_data.get("cover_image")
                existing_book.amazon_link = book_data.get("amazon_link")
                db.session.commit()
                print(f"Book with ISBN {book_data['isbn']} updated.")
            else:
                # Add new book
                author = authors_dict.get(book_data["author_username"])
                if author:
                    book = Book(
                        title=book_data["title"],
                        isbn=book_data["isbn"],
                        description=book_data["description"],
                        price=book_data["price"],
                        stock=book_data["stock"],
                        pages=book_data["pages"],
                        edition=book_data["edition"],
                        publisher_name=book_data["publisher_name"],
                        subject=book_data["subject"],
                        exam_type=book_data["exam_type"],
                        language=book_data["language"],
                        category=book_data["category"],
                        keywords=book_data["keywords"],
                        author_id=author.id,
                        cover_image=book_data.get("cover_image"),
                        amazon_link=book_data.get("amazon_link")
                    )
                    db.session.add(book)
                    db.session.commit()
                    print(f"Book with ISBN {book_data['isbn']} added.")
                else:
                    print(f"Author with username '{book_data['author_username']}' not found. Skipping book with ISBN {book_data['isbn']}.")
        
        db.session.commit()
        print("Sample data populated successfully!")

        # Add demo notifications for admin accounts
        from models import User
        from advanced_routes import create_notification
        admin_users = User.query.filter_by(role='publisher').all()
        for admin in admin_users:
            create_notification(
                admin.id,
                'Welcome to the Admin Dashboard!',
                'This is a demo notification. You will see order updates, user messages, and system alerts here.',
                'system',
            )
            create_notification(
                admin.id,
                'Order Cancelled by User',
                'Order #1001 by John Doe has been cancelled. Reason: Changed mind.',
                'order',
            )
            create_notification(
                admin.id,
                'Low Stock Alert',
                'Book "Indian Polity by M. Laxmikanth" is low on stock. Only 5 copies left.',
                'stock',
            )

        # Add initial users for Publisher, Author, Vendor, Student
        initial_users = [
            {"username": "publisher_admin", "email": "publisher@example.com", "full_name": "Publisher Admin", "role": "publisher", "password": "admin123"},
            {"username": "author_navjot", "email": "author@example.com", "full_name": "Author Navjot", "role": "author", "password": "author123"},
            {"username": "vendor_distributor", "email": "vendor@example.com", "full_name": "Vendor Distributor", "role": "vendor", "password": "vendor123"},
            {"username": "student_buyer", "email": "student@example.com", "full_name": "Student Buyer", "role": "student", "password": "student123"},
        ]
        for user_data in initial_users:
            if not User.query.filter_by(username=user_data["username"]).first():
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    role=user_data["role"]
                )
                user.set_password(user_data["password"])
                db.session.add(user)
        db.session.commit()

if __name__ == "__main__":
    populate_sample_data()
