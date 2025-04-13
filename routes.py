from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import app, db
from models import Hotel, Flight, Package, Chatbot, Search, User, OTP, Booking, PasswordResetToken
import logging
from datetime import datetime
from email_validator import validate_email, EmailNotValidError

# Home route
@app.route('/')
def index():
    # Get featured items for each category
    hotels = Hotel.get_all_hotels()
    flights = Flight.get_all_flights()
    packages = Package.get_all_packages()
    
    # Take only top 3 for each category for featured display
    featured_hotels = hotels[:3] if hotels else []
    featured_flights = flights[:3] if flights else []
    featured_packages = packages[:3] if packages else []
    
    return render_template('index.html', 
                          hotels=featured_hotels, 
                          flights=featured_flights, 
                          packages=featured_packages)

# Hotels route
@app.route('/hotels')
def hotels():
    hotels = Hotel.get_all_hotels()
    return render_template('hotels.html', hotels=hotels)

# Hotel detail route
@app.route('/hotel/<int:hotel_id>')
def hotel_detail(hotel_id):
    hotel = Hotel.get_hotel_by_id(hotel_id)
    if not hotel:
        flash('Hotel not found', 'error')
        return redirect(url_for('hotels'))
    return render_template('hotel_detail.html', hotel=hotel)

# Flights route
@app.route('/flights')
def flights():
    flights = Flight.get_all_flights()
    return render_template('flights.html', flights=flights)

# Flight detail route
@app.route('/flight/<int:flight_id>')
def flight_detail(flight_id):
    flight = Flight.get_flight_by_id(flight_id)
    if not flight:
        flash('Flight not found', 'error')
        return redirect(url_for('flights'))
    return render_template('flight_detail.html', flight=flight)

# Packages route
@app.route('/packages')
def packages():
    packages = Package.get_all_packages()
    return render_template('packages.html', packages=packages)

# Package detail route
@app.route('/package/<int:package_id>')
def package_detail(package_id):
    package = Package.get_package_by_id(package_id)
    if not package:
        flash('Package not found', 'error')
        return redirect(url_for('packages'))
    return render_template('package_detail.html', package=package)

# Search route
@app.route('/search')
def search():
    query = request.args.get('query', '')
    if not query:
        return redirect(url_for('index'))
    
    results = Search.search_all(query)
    return render_template('search.html', 
                          query=query, 
                          hotels=results['hotels'], 
                          flights=results['flights'], 
                          packages=results['packages'])

# Chatbot API endpoint
@app.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Special case for OTP resend
    if message.lower() == 'resend otp' and current_user.is_authenticated:
        # Generate and "send" OTP
        otp = OTP.generate_otp(current_user.email, 'booking')
        
        # In a real app, we would send an email/SMS with the OTP
        return jsonify({'response': f'Your new OTP is: {otp}. In a real system, this would be sent securely to your email or phone.'})
    
    response = Chatbot.get_response(message)
    return jsonify({'response': response})

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Validate form data
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
            
        # Validate email format
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            flash(str(e), 'error')
            return render_template('register.html')
            
        # Check if username or email already exists
        if User.get_by_username(username):
            flash('Username already exists', 'error')
            return render_template('register.html')
            
        if User.get_by_email(email):
            flash('Email already exists', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
            
        # Check if user exists (by username or email)
        user = User.get_by_username(username)
        if not user:
            user = User.get_by_email(username)  # Allow login with email too
            
        if not user:
            flash('No account found with that username or email', 'error')
            return render_template('login.html')
            
        if not user.check_password(password):
            flash('Incorrect password. Please try again', 'error')
            return render_template('login.html')
            
        # Log the user in
        login_user(user, remember=remember)
        
        # Redirect to requested page or index
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
            
        flash('Login successful', 'success')
        return redirect(next_page)
        
    return render_template('login.html')

# User Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successful', 'success')
    return redirect(url_for('index'))

# User Profile
@app.route('/profile')
@login_required
def profile():
    # Get user's bookings
    bookings = Booking.get_user_bookings(current_user.id)
    return render_template('profile.html', user=current_user, bookings=bookings)

# Forgot Password
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Email is required', 'error')
            return render_template('forgot_password.html')
            
        # Validate email format
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            flash(str(e), 'error')
            return render_template('forgot_password.html')
            
        # Check if user exists
        user = User.get_by_email(email)
        if not user:
            # Don't reveal whether email exists for security
            flash('If your email is registered, you will receive a password reset link', 'info')
            return render_template('forgot_password.html')
            
        # Generate reset token
        token = PasswordResetToken.generate_token(user)
        
        # In a real app, we would send an email here
        # For demonstration purposes, we'll just show the token
        reset_link = url_for('reset_password', token=token, _external=True)
        
        flash(f'Password reset link: {reset_link}', 'info')
        return render_template('forgot_password.html', reset_link=reset_link)
        
    return render_template('forgot_password.html')

# Reset Password
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    user = PasswordResetToken.verify_token(token)
    if not user:
        flash('Invalid or expired token', 'error')
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('reset_password.html', token=token)
            
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html', token=token)
            
        # Update password
        user.set_password(password)
        
        # Mark token as used
        token_obj = PasswordResetToken.query.filter_by(token=token).first()
        token_obj.used = True
        
        db.session.commit()
        
        flash('Password reset successful. Please log in with your new password.', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html', token=token)

# Booking process - Step 1: Basic details
@app.route('/booking/step1/<booking_type>/<int:item_id>', methods=['GET', 'POST'])
@login_required
def booking_step1(booking_type, item_id):
    # Validate booking type
    if booking_type not in ['hotel', 'flight', 'package']:
        flash('Invalid booking type', 'error')
        return redirect(url_for('index'))
        
    # Get item details
    item = None
    if booking_type == 'hotel':
        item = Hotel.get_hotel_by_id(item_id)
    elif booking_type == 'flight':
        item = Flight.get_flight_by_id(item_id)
    elif booking_type == 'package':
        item = Package.get_package_by_id(item_id)
        
    if not item:
        flash(f'{booking_type.capitalize()} not found', 'error')
        return redirect(url_for(f'{booking_type}s'))
    
    # Add today's date for the date picker min value
    today = datetime.now().strftime('%Y-%m-%d')
        
    if request.method == 'POST':
        # Process form data
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date', None)
        adults = int(request.form.get('adults', 1))
        children = int(request.form.get('children', 0))
        
        # Validate data
        if not start_date_str:
            flash('Start date is required', 'error')
            return render_template('booking_step1.html', booking_type=booking_type, item=item)
            
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
        except ValueError:
            flash('Invalid date format', 'error')
            return render_template('booking_step1.html', booking_type=booking_type, item=item)
            
        # Calculate total price (simplified)
        base_price = float(item.price)
        total_price = base_price * adults + (base_price * 0.5 * children)
        
        # For packages and hotels, multiply by number of days
        if booking_type in ['hotel', 'package'] and end_date:
            days = (end_date - start_date).days
            if days > 0:
                total_price *= days
        
        # Make the session permanent to ensure it persists across requests
        session.permanent = True
        
        # Store all booking details in session at once, including total price
        session['booking'] = {
            'booking_type': booking_type,
            'item_id': item_id,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'adults': adults,
            'children': children,
            'total_price': total_price,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Add timestamp for debugging
        }
        
        # Log session data for debugging
        logging.debug(f"Session booking data set: {session['booking']}")
        
        # Force session to be saved
        session.modified = True
        
        # Add a flash message to display the booking details
        flash(f'Booking details: {booking_type.capitalize()} booking for {adults} adults and {children} children. Total: ₹{total_price:.2f}', 'info')
        
        # Move to OTP verification, but include booking info in the URL as a fallback
        # This way, if the session data is lost, we can still recover it
        return redirect(url_for('booking_step2', 
                               booking_type=booking_type, 
                               item_id=item_id, 
                               fallback=1))
        
    return render_template('booking_step1.html', booking_type=booking_type, item=item, today=today)

# Debug endpoint to show session data
@app.route('/debug/session')
@login_required
def debug_session():
    import json
    from flask import jsonify
    
    # Only show this in development
    if app.debug:
        # Get all session data and return as JSON
        session_data = dict(session)
        return jsonify(session_data)
    else:
        return "Debug endpoints disabled in production", 403

# Booking process - Step 2: OTP verification
@app.route('/booking/step2', methods=['GET', 'POST'])
@login_required
def booking_step2():
    # Log session keys for debugging
    logging.debug(f"Session keys in booking_step2: {list(session.keys())}")
    
    # Add debugging in case of session issues
    # To prevent possible session loss, try to pass the data as a parameter if necessary
    item_id = request.args.get('item_id')
    booking_type = request.args.get('booking_type')
    is_fallback = request.args.get('fallback')
    
    # Check if booking details exist in session
    if 'booking' not in session:
        logging.error("No booking data found in session!")
        
        # If we have fallback data in the URL, try to reconstruct the session
        if is_fallback and item_id and booking_type:
            logging.info(f"Attempting to recover session from URL params: type={booking_type}, id={item_id}")
            
            try:
                # Get item details
                item = None
                if booking_type == 'hotel':
                    item = Hotel.get_hotel_by_id(int(item_id))
                elif booking_type == 'flight':
                    item = Flight.get_flight_by_id(int(item_id))
                elif booking_type == 'package':
                    item = Package.get_package_by_id(int(item_id))
                
                if item:
                    # We have the item, but we're missing other details
                    # Create a minimal booking entry to allow the user to continue
                    today = datetime.now()
                    tomorrow = today + timedelta(days=1)
                    
                    # Basic booking data with defaults
                    session['booking'] = {
                        'booking_type': booking_type,
                        'item_id': int(item_id),
                        'start_date': today.strftime('%Y-%m-%d'),
                        'end_date': tomorrow.strftime('%Y-%m-%d'),
                        'adults': 1,
                        'children': 0,
                        'total_price': float(item.price),
                        'recovered': True,  # Flag to indicate this was recovered
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    session.permanent = True
                    session.modified = True
                    
                    flash('We recovered your booking information. Please confirm the OTP to continue.', 'success')
                    logging.info("Session recovery successful from URL parameters")
                    
                    # Proceed with the recovered data
                    booking_data = session['booking']
                    # Generate a new OTP since we're reconstructing the session
                    otp = OTP.generate_otp(current_user.email, 'booking')
                    flash(f'A verification code has been sent to your email address ({current_user.email}).', 'info')
                    return render_template('booking_step2.html', booking_data=booking_data)
            except Exception as e:
                logging.error(f"Error during session recovery: {str(e)}")
        
        # If recovery wasn't possible or unsuccessful
        flash('No booking data found. This could be due to session timeout or browser issues.', 'error')
        
        # Create a debug link
        debug_url = url_for('debug_session')
        flash(f'<a href="{debug_url}" target="_blank">View session debug info</a>', 'info')
        
        # Redirect based on the context if we have some data
        if item_id and booking_type:
            flash('Attempting to restart your booking...', 'info')
            return redirect(url_for('booking_step1', booking_type=booking_type, item_id=item_id))
        
        return redirect(url_for('index'))
    
    # Get booking data from session
    booking_data = session['booking']
    logging.debug(f"Retrieved booking data from session: {booking_data}")
        
    if request.method == 'GET':
        # Generate and send OTP when first accessing the verification page
        otp = OTP.generate_otp(current_user.email, 'booking')
        
        # Inform user that OTP has been sent
        flash(f'A verification code has been sent to your email address ({current_user.email}).', 'info')
        flash('Please check your inbox (and spam folder) for the verification code.', 'info')
        return render_template('booking_step2.html', booking_data=booking_data)
            
    elif request.method == 'POST':
        # Verify OTP
        otp_code = request.form.get('otp')
        
        if not otp_code:
            flash('Please enter the verification code (OTP) to continue', 'error')
            return render_template('booking_step2.html', booking_data=booking_data)
            
        if OTP.verify_otp(current_user.email, otp_code, 'booking'):
            # OTP is valid, create booking
            # Create new booking
            booking = Booking(
                user_id=current_user.id,
                booking_type=booking_data['booking_type'],
                item_id=booking_data['item_id'],
                start_date=datetime.strptime(booking_data['start_date'], '%Y-%m-%d'),
                end_date=datetime.strptime(booking_data['end_date'], '%Y-%m-%d') if booking_data.get('end_date') else None,
                adults=booking_data['adults'],
                children=booking_data['children'],
                total_price=booking_data['total_price'],
                status='confirmed'  # Auto-confirm for demonstration
            )
            
            db.session.add(booking)
            db.session.commit()
            
            # Clear booking from session
            session.pop('booking', None)
            
            flash('Booking confirmed successfully!', 'success')
            return redirect(url_for('booking_confirmation', booking_id=booking.id))
        else:
            flash('Invalid or expired verification code. Please try again or request a new code.', 'error')
            return render_template('booking_step2.html', booking_data=booking_data)
    
    return render_template('booking_step2.html', booking_data=session.get('booking', {}))

# Booking confirmation
@app.route('/booking/confirmation/<int:booking_id>')
@login_required
def booking_confirmation(booking_id):
    # Get booking details
    booking = Booking.query.get(booking_id)
    
    if not booking or booking.user_id != current_user.id:
        flash('Booking not found', 'error')
        return redirect(url_for('profile'))
        
    # Get item details
    item = booking.get_item_details()
    
    # For the booking confirmation template, we need to add timedelta
    from datetime import timedelta
    
    return render_template('booking_confirmation.html', booking=booking, item=item, timedelta=timedelta)

# Manage booking (cancel/modify)
@app.route('/booking/manage/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def manage_booking(booking_id):
    # Get booking details
    booking = Booking.query.get(booking_id)
    
    if not booking or booking.user_id != current_user.id:
        flash('Booking not found', 'error')
        return redirect(url_for('profile'))
            
    # Get item details
    item = booking.get_item_details()
    
    # Add today's date for the date picker min value
    today = datetime.now().strftime('%Y-%m-%d')
    
    # For the booking confirmation template, we need to add timedelta
    from datetime import timedelta
    
    return render_template('manage_booking.html', booking=booking, item=item, timedelta=timedelta, today=today)

# Handle booking cancellation
@app.route('/booking/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get(booking_id)
    
    if not booking or booking.user_id != current_user.id:
        flash('Booking not found', 'error')
        return redirect(url_for('profile'))
        
    reason = request.form.get('reason')
    other_reason = request.form.get('other_reason')
    confirm = request.form.get('confirm')
    
    if not confirm or not reason:
        flash('Please confirm cancellation and provide a reason', 'warning')
        return redirect(url_for('manage_booking', booking_id=booking_id))
    
    # Log the cancellation reason
    cancellation_reason = other_reason if reason == 'other' and other_reason else reason
    logging.info(f"Booking {booking_id} cancelled. Reason: {cancellation_reason}")
    
    # Cancel booking
    booking.status = 'cancelled'
    db.session.commit()
    
    flash('Booking cancelled successfully', 'success')
    return redirect(url_for('profile'))

# Handle booking updates
@app.route('/booking/update/<int:booking_id>', methods=['POST'])
@login_required
def update_booking(booking_id):
    booking = Booking.query.get(booking_id)
    
    if not booking or booking.user_id != current_user.id:
        flash('Booking not found', 'error')
        return redirect(url_for('profile'))
        
    if booking.status == 'cancelled':
        flash('Cannot update a cancelled booking', 'error')
        return redirect(url_for('manage_booking', booking_id=booking_id))
    
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    adults = int(request.form.get('adults', 1))
    children = int(request.form.get('children', 0))
    confirm = request.form.get('confirm')
    
    if not confirm or not start_date_str:
        flash('Please confirm the changes and provide required details', 'warning')
        return redirect(url_for('manage_booking', booking_id=booking_id))
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
        
        # Update booking
        booking.start_date = start_date
        booking.end_date = end_date
        booking.adults = adults
        booking.children = children
        
        # Recalculate price based on new details
        item = booking.get_item_details()
        base_price = float(item.price)
        total_price = base_price * adults + (base_price * 0.5 * children)
        
        # For packages and hotels, multiply by number of days
        if booking.booking_type in ['hotel', 'package'] and end_date:
            days = (end_date - start_date).days
            if days > 0:
                total_price *= days
                
        booking.total_price = total_price
        db.session.commit()
        
        flash('Booking updated successfully', 'success')
    except ValueError:
        flash('Invalid date format', 'error')
    
    return redirect(url_for('manage_booking', booking_id=booking_id))

# Resend OTP for booking
@app.route('/booking/resend-otp')
@login_required
def resend_otp():
    # Log session keys for debugging
    logging.debug(f"Session keys in resend_otp: {list(session.keys())}")
    
    # Check if booking details exist in session
    if 'booking' not in session:
        logging.error("No booking data found in session during OTP resend!")
        flash('No booking in progress', 'error')
        return redirect(url_for('index'))
    
    # Log booking data
    logging.debug(f"Booking data in resend_otp: {session['booking']}")
    
    # Generate and send OTP
    otp = OTP.generate_otp(current_user.email, 'booking')
    logging.debug(f"Generated new OTP for {current_user.email}: {otp}")
    
    # Inform user that OTP has been sent
    flash(f'A new verification code has been sent to your email address ({current_user.email}).', 'info')
    flash('Please check your inbox (and spam folder) for the verification code.', 'info')
    
    # Set permanent session
    session.permanent = True
    session.modified = True
    
    # When redirecting, include booking data in the URL as a fallback
    booking_data = session['booking']
    return redirect(url_for('booking_step2', 
                           booking_type=booking_data['booking_type'], 
                           item_id=booking_data['item_id'], 
                           fallback=1))

# Update user profile
@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    
    if not username or not email:
        flash('Username and email are required', 'error')
        return redirect(url_for('profile'))
    
    # Check if new username or email already exists (if changed)
    if username != current_user.username and User.get_by_username(username):
        flash('Username already taken', 'error')
        return redirect(url_for('profile'))
        
    if email != current_user.email and User.get_by_email(email):
        flash('Email already in use', 'error')
        return redirect(url_for('profile'))
    
    # Update user
    current_user.username = username
    current_user.email = email
    current_user.first_name = first_name
    current_user.last_name = last_name
    
    db.session.commit()
    flash('Profile updated successfully', 'success')
    return redirect(url_for('profile'))

# Change password
@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_new_password')
    
    if not all([current_password, new_password, confirm_password]):
        flash('All fields are required', 'error')
        return redirect(url_for('profile'))
        
    if new_password != confirm_password:
        flash('New passwords do not match. Please ensure both entries are identical.', 'error')
        return redirect(url_for('profile'))
        
    if not current_user.check_password(current_password):
        flash('Current password is incorrect. Please check and try again.', 'error')
        return redirect(url_for('profile'))
    
    # Update password
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Password changed successfully', 'success')
    return redirect(url_for('profile'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    logging.error(f"Server error: {e}")
    return render_template('index.html', error="Internal server error"), 500
