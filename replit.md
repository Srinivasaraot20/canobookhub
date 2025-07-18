# CanoBookHub - Academic Book Publication Platform

## Overview

CanoBookHub is a comprehensive book publication and sales platform designed for academic and competitive exam preparation materials. The platform serves multiple user roles including publishers, authors, vendors/distributors, and students/buyers, providing a complete ecosystem for book management, sales, and distribution.

## User Preferences

Preferred communication style: Simple, everyday language.
Visual theme: Active black theme with modern contrast and neon accents.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with PostgreSQL (configured via DATABASE_URL environment variable)
- **Authentication**: Flask-Login for session management
- **Database Migrations**: Flask-Migrate for schema management
- **File Handling**: Werkzeug for secure file uploads

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 dark theme
- **CSS Framework**: Bootstrap 5 with active black theme customization
- **Theme Colors**: Deep black (#0a0a0a) with cyan accent (#00d4ff) and neon green (#00ff88)
- **JavaScript**: Vanilla JavaScript with Bootstrap components
- **Icons**: Font Awesome 6.0
- **Responsive Design**: Mobile-first approach with smooth animations

### Security & Configuration
- **Session Management**: Flask sessions with secret key from environment
- **Proxy Support**: ProxyFix middleware for proper URL generation behind proxies
- **File Upload Security**: Restricted file types and size limits (16MB max)
- **Password Security**: Werkzeug password hashing

## Key Components

### User Management System
- **Multi-role authentication**: Publisher (super admin), Author, Vendor/Distributor, Student/Buyer
- **User profiles**: Full name, email, phone, address, role-based permissions
- **Password security**: Hashed passwords with secure validation

### Book Management
- **Book catalog**: Title, ISBN, description, pricing, stock management
- **Metadata**: Pages, edition, publisher, subject, exam type categorization
- **File management**: Cover images and sample PDFs
- **Pricing tiers**: Regular and wholesale pricing for different user roles

### Order Management
- **Shopping cart**: Session-based cart functionality
- **Order processing**: Order number generation, status tracking
- **Payment integration**: Multiple payment methods supported
- **Order fulfillment**: Status tracking from pending to delivered

### Royalty Management
- **Royalty tracking**: Percentage-based royalty calculation per book
- **Sales analytics**: Track sales count and earnings per author/book
- **Payment management**: Mark royalty payments as paid/pending
- **Reporting**: Generate royalty reports for authors and publishers

### Document Management
- **Secure storage**: Contract, agreement, and legal document storage
- **Access control**: Role-based document access (authors see only their documents)
- **File types**: Support for contracts, PAN, Aadhaar, bank details
- **Document tagging**: Link documents to specific authors/books

## Data Flow

### User Registration & Authentication
1. User selects role during registration (publisher/author/vendor/student)
2. Form validation ensures required fields and role-specific data
3. Password hashing before database storage
4. Session management for authenticated users

### Book Catalog & Discovery
1. Publishers upload books with metadata and media files
2. Books categorized by exam type (UPSC, JEE, NEET, SSC, etc.)
3. Search and filtering functionality across multiple attributes
4. Role-based pricing display (wholesale for vendors)

### Order Processing
1. Users add books to cart (session-based storage)
2. Checkout process collects shipping and payment information
3. Order number generation and database persistence
4. Royalty calculation and tracking updates
5. Order status updates and notifications

### Royalty & Document Workflows
1. Publishers define royalty percentages per book/author
2. Sales automatically update royalty calculations
3. Documents uploaded with proper access controls
4. Authors can view earnings and download relevant documents

## External Dependencies

### Python Packages
- **Flask**: Web framework and extensions (SQLAlchemy, Login, Migrate, WTF)
- **Werkzeug**: Security utilities and file handling
- **WTForms**: Form validation and rendering
- **SQLAlchemy**: Database ORM and migrations

### Frontend Libraries
- **Bootstrap 5**: CSS framework with dark theme
- **Font Awesome**: Icon library
- **Custom CSS**: Application-specific styling

### File System
- **Static uploads**: Local file storage for book covers and documents
- **Media handling**: Secure file upload with type validation

## Deployment Strategy

### Environment Configuration
- **Database URL**: PostgreSQL connection via DATABASE_URL environment variable
- **Session Secret**: Secure session management via SESSION_SECRET
- **File Storage**: Local uploads directory with proper permissions

### Application Structure
- **Single Flask app**: Centralized application instance with extensions
- **Template organization**: Role-based dashboard templates
- **Static assets**: Organized CSS, JS, and upload directories

### Database Schema
- **Users**: Multi-role user management with relationships
- **Books**: Complete book catalog with metadata
- **Orders**: Order processing with item tracking
- **Royalties**: Author royalty management
- **Documents**: Secure document storage and access

### Recent Updates (2025-01-13)
- **Active Black Theme**: Implemented comprehensive dark theme with modern aesthetics
  - Deep black backgrounds with cyan and neon green accents
  - Smooth hover animations and glowing effects
  - Professional gradient buttons and interactive elements
  - Custom scrollbar and enhanced visual hierarchy
- **Email Integration**: Complete SMTP email service with Gmail
  - Order confirmation emails with invoice details
  - Status update notifications for customers
  - Automated email dispatch system
- **Order Tracking**: Advanced timeline-based order tracking
  - Visual progress indicators for order status
  - Detailed order history and tracking pages
  - Publisher order management with status updates
- **Template System**: All dashboard templates and error pages implemented
- **Navigation**: Enhanced navigation with Orders section and user dropdowns