import os
import logging
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
load_dotenv()  # This loads the variables from .env



# Configure logging
logging.basicConfig(level=logging.DEBUG)
# Enable Flask's own debug logging
app_logger = logging.getLogger('flask')
app_logger.setLevel(logging.DEBUG)
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.DEBUG)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Initialize LoginManager
login_manager = LoginManager()

# Initialize Flask-Mail
mail = Mail()

# Create the Flask application
app = Flask(__name__)
app.debug = True
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

# Configure the database using the DATABASE_URL environment variable
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/travel_db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Email configuration (for sending OTP)
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")  # Default to Gmail SMTP
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", "587"))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "True") == "True"
app.config["MAIL_USE_SSL"] = os.environ.get("MAIL_USE_SSL", "False") == "True"
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", os.environ.get("MAIL_USERNAME", "noreply@TravelWise.com"))
app.config["MAIL_DEBUG"] = app.debug  # Use app's debug setting for mail debugging

# Initialize SQLAlchemy with the app
db.init_app(app)

# Initialize Flask-Login
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

# Initialize Flask-Mail
mail.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Initialize the app context
with app.app_context():
    # Import models
    import models
    
    # Create all tables
    db.create_all()
    
    # Seed default chatbot responses
    models.ChatbotResponse.seed_default_responses()
    
    # Seed sample data for hotels, flights, and packages if they don't exist
    def seed_sample_data():
        # Check if we already have data
        if models.Hotel.query.count() == 0:
            # Sample hotels
            sample_hotels = [
                models.Hotel(
                    name="Luxury Beach Resort",
                    location="Maldives",
                    price=450.00,
                    rating=4.8,
                    description="Experience paradise with overwater bungalows and private beaches.",
                    image_url="https://images.unsplash.com/photo-1566073771259-6a8506099945?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                ),
                models.Hotel(
                    name="Mountain View Lodge",
                    location="Switzerland",
                    price=320.00,
                    rating=4.6,
                    description="Cozy alpine lodge with stunning views of the Swiss Alps.",
                    image_url="https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                ),
                models.Hotel(
                    name="City Center Hotel",
                    location="New York",
                    price=280.00,
                    rating=4.4,
                    description="Modern hotel in the heart of Manhattan, walking distance to major attractions.",
                    image_url="https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                ),
                models.Hotel(
                    name="Historic Grand Hotel",
                    location="Paris",
                    price=380.00,
                    rating=4.7,
                    description="Elegant 19th century hotel with views of the Eiffel Tower.",
                    image_url="https://images.unsplash.com/photo-1551632436-cbf8dd35adfa?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                ),
                models.Hotel(
                    name="Seaside Inn",
                    location="Santorini",
                    price=290.00,
                    rating=4.5,
                    description="Charming inn with whitewashed walls and stunning caldera views.",
                    image_url="https://images.unsplash.com/photo-1570213489059-0aac6626cade?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                )
            ]
            
            # Add sample hotels to the database
            for hotel in sample_hotels:
                db.session.add(hotel)
            
            logging.info("Sample hotels added successfully")
        
        # Sample flights
        if models.Flight.query.count() == 0:
            from datetime import datetime, timedelta
            
            # Calculate departure times (starting from today)
            now = datetime.now()
            sample_flights = [
                models.Flight(
                    airline="Global Airways",
                    departure_city="New York",
                    arrival_city="London",
                    departure_time=now + timedelta(days=1, hours=8),
                    arrival_time=now + timedelta(days=1, hours=20),
                    price=550.00,
                    description="Direct overnight flight with in-flight entertainment and meal service."
                ),
                models.Flight(
                    airline="Pacific Express",
                    departure_city="Los Angeles",
                    arrival_city="Tokyo",
                    departure_time=now + timedelta(days=3, hours=10),
                    arrival_time=now + timedelta(days=4, hours=2),
                    price=820.00,
                    description="Long-haul flight with premium economy options and multiple meal services."
                ),
                models.Flight(
                    airline="Euro Connect",
                    departure_city="Paris",
                    arrival_city="Rome",
                    departure_time=now + timedelta(days=2, hours=14),
                    arrival_time=now + timedelta(days=2, hours=16, minutes=30),
                    price=180.00,
                    description="Short European hop with complimentary beverage service."
                ),
                models.Flight(
                    airline="Southern Skies",
                    departure_city="Sydney",
                    arrival_city="Auckland",
                    departure_time=now + timedelta(days=5, hours=9),
                    arrival_time=now + timedelta(days=5, hours=14),
                    price=240.00,
                    description="Trans-Tasman flight with spectacular views."
                ),
                models.Flight(
                    airline="Desert Air",
                    departure_city="Dubai",
                    arrival_city="Cairo",
                    departure_time=now + timedelta(days=4, hours=12),
                    arrival_time=now + timedelta(days=4, hours=16),
                    price=320.00,
                    description="Middle Eastern connection with premium service options."
                )
            ]
            
            # Add sample flights to the database
            for flight in sample_flights:
                db.session.add(flight)
            
            logging.info("Sample flights added successfully")
        
        # Sample packages
        if models.Package.query.count() == 0:
            sample_packages = [
                models.Package(
                    name="Mediterranean Cruise",
                    description="7-day luxury cruise stopping at ports in Italy, Greece, and Croatia.",
                    destination="Mediterranean Sea",
                    duration=7,
                    price=1200.00,
                    included_services="Accommodation, meals, onboard entertainment, guided shore excursions",
                    image_url="https://images.unsplash.com/photo-1548574505-5e239809ee19?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                ),
                models.Package(
                    name="African Safari Adventure",
                    description="10-day safari through national parks in Kenya and Tanzania.",
                    destination="East Africa",
                    duration=10,
                    price=2800.00,
                    included_services="Accommodation, meals, game drives, park fees, local guides",
                    image_url="https://images.unsplash.com/photo-1523805009345-7448845a9e53?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                ),
                models.Package(
                    name="Island Hopping Thailand",
                    description="12-day tour through Bangkok and the beautiful islands of southern Thailand.",
                    destination="Thailand",
                    duration=12,
                    price=1500.00,
                    included_services="Accommodation, breakfast, transportation between islands, select activities",
                    image_url="https://images.unsplash.com/photo-1552465011-b4e21bf6e79a?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                ),
                models.Package(
                    name="European Capitals Express",
                    description="8-day train journey connecting Paris, Amsterdam, Berlin, and Prague.",
                    destination="Europe",
                    duration=8,
                    price=1800.00,
                    included_services="First-class train tickets, 4-star hotels, daily breakfast, city passes",
                    image_url="https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                ),
                models.Package(
                    name="Inca Trail to Machu Picchu",
                    description="6-day hiking adventure through the Andes to the ancient Inca citadel.",
                    destination="Peru",
                    duration=6,
                    price=1100.00,
                    included_services="Guided trek, camping equipment, meals, entrance fees, return train journey",
                    image_url="https://images.unsplash.com/photo-1526392060635-9d6019884377?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                )
            ]
            
            # Add sample packages to the database
            for package in sample_packages:
                db.session.add(package)
            
            logging.info("Sample packages added successfully")
        
        # Commit all changes
        db.session.commit()
    
    # Seed sample data
    seed_sample_data()
    
    # Import routes after app initialization to avoid circular imports
    import routes
