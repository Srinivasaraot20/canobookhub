import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from flask import render_template_string
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.username = "srinurao1902@gmail.com"
        self.password = "dvot liyz xxgc zdmh"
        
    def send_email(self, to_email, subject, body_html, body_text=None, attachments=None):
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text version if provided
            if body_text:
                text_part = MIMEText(body_text, 'plain')
                msg.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(body_html, 'html')
            msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_order_confirmation(self, user, order):
        """Send order confirmation email (no PDF invoice attached)"""
        subject = f"Order Confirmation - #{order.order_number}"
        expected_delivery = (order.created_at + timedelta(days=5)).strftime('%B %d, %Y')
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
                .content {{ padding: 20px; }}
                .order-details {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; }}
                .btn {{ background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Order Confirmation</h1>
                    <p>Thank you for your order!</p>
                </div>
                
                <div class="content">
                    <h2>Hello {user.full_name},</h2>
                    <p>Your order has been confirmed and is being processed.</p>
                    
                    <div class="order-details">
                        <h3>Order Details</h3>
                        <p><strong>Order Number:</strong> {order.order_number}</p>
                        <p><strong>Order Date:</strong> {order.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                        <p><strong>Total Amount:</strong> ₹{order.total_amount:.2f}</p>
                        <p><strong>Payment Status:</strong> {order.payment_status.title()}</p>
                        <p><strong>Order Status:</strong> {order.status.title()}</p>
                        <p><strong>Expected Delivery:</strong> {expected_delivery}</p>
                    </div>
                    
                    <h3>Items Ordered</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Book Title</th>
                                <th>Quantity</th>
                                <th>Price</th>
                                <th>Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f"<tr><td>{item.book.title}</td><td>{item.quantity}</td><td>₹{item.price:.2f}</td><td>₹{item.price * item.quantity:.2f}</td></tr>" for item in order.items])}
                        </tbody>
                    </table>
                    
                    <div class="order-details">
                        <h3>Shipping Address</h3>
                        <p>{order.shipping_address}</p>
                    </div>
                    
                    <p>We'll send you another email when your order ships.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:5000/orders/{order.id}" class="btn">Track Your Order</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Thank you for choosing CanoBookHub!</p>
                    <p>If you have any questions, please contact us at support@canobookhub.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        attachments = None
        return self.send_email(user.email, subject, html_body, attachments=attachments)
    
    def send_order_status_update(self, order, user, new_status):
        """Send order status update email"""
        subject = f"Order Update - #{order.order_number}"
        
        status_messages = {
            'confirmed': 'Your order has been confirmed and is being prepared.',
            'shipped': 'Great news! Your order has been shipped and is on its way.',
            'delivered': 'Your order has been delivered. Thank you for your business!',
            'cancelled': 'Your order has been cancelled. If you have any questions, please contact us.'
        }
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
                .content {{ padding: 20px; }}
                .status-update {{ background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745; }}
                .footer {{ text-align: center; padding: 20px; color: #666; }}
                .btn {{ background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Order Status Update</h1>
                    <p>Order #{order.order_number}</p>
                </div>
                
                <div class="content">
                    <h2>Hello {user.full_name},</h2>
                    
                    <div class="status-update">
                        <h3>Status: {new_status.title()}</h3>
                        <p>{status_messages.get(new_status, 'Your order status has been updated.')}</p>
                    </div>
                    
                    <p><strong>Order Date:</strong> {order.created_at.strftime('%B %d, %Y')}</p>
                    <p><strong>Total Amount:</strong> ₹{order.total_amount:.2f}</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:5000/orders/{order.id}" class="btn">View Order Details</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Thank you for choosing CanoBookHub!</p>
                    <p>If you have any questions, please contact us at support@canobookhub.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user.email, subject, html_body)

# Create global instance
email_service = EmailService()