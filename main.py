
from flask import Flask, render_template, request, redirect, url_for, flash, request, session
from flask import session, request, redirect, url_for, flash, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.functions import user
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from sqlalchemy import text
import psycopg2
from psycopg2 import sql
from flask_migrate import Migrate
from datetime import datetime
db = SQLAlchemy()
try:
    # Attempt to connect to the PostgreSQL database
    conn = psycopg2.connect(
        host="localhost",
        dbname="zero_hunger",
        user="postgres",
        password="1234",
        port="5432"
    )
    print("Connected to the database successfully")



except psycopg2.DatabaseError as e:
    # Catch and print any database errors
    print(f"Failed to connect to the database or create tables: {e}")


app = Flask(__name__)
@app.route('/')
def home():
    return redirect(url_for('login'))


from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

app.secret_key = 'your_secret_key_here'  # Required for session management
# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/zero_hunger'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Admin Model
class Admin(db.Model):
    __tablename__ = 'admin'
    admin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)



class AdminItem(db.Model):
    __tablename__ = 'admin_items'
    item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(255), unique=True, nullable=False)
    market_price = db.Column(db.Numeric(10, 2), nullable=False)

class DistributorItem(db.Model):
    __tablename__ = 'distributor_items'
    item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    distributor_id = db.Column(db.Integer, db.ForeignKey('food_distributors.distributor_id'))  # Foreign key reference
    __table_args__ = (db.UniqueConstraint('item_id', 'distributor_id', name='unique_item_distributor'),)


class Farmer(db.Model):
    __tablename__ = 'farmers'
    farmer_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(15))
    location = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')

    # Relationships
    items = db.relationship('Item', back_populates='farmer')
    orders = db.relationship('Order', back_populates='farmer', lazy=True)


class PendingItem(db.Model):
    __tablename__ = 'pending_items'
    pending_item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(255), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.farmer_id'), nullable=False)
    stock = db.Column(db.Integer, nullable=True)  # Ensure stock is required and not null

class FoodDistributor(db.Model):
    __tablename__ = 'food_distributors'

    distributor_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    contact_number = db.Column(db.String(15))
    location = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')

    orders = db.relationship('Order', back_populates='distributor', lazy=True)  # Correct back reference




class DistributionRequest(db.Model):
    __tablename__ = 'distribution_requests'

    request_id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('food_distributors.distributor_id'), nullable=False)
    request_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='pending')  # e.g., 'pending', 'approved', 'rejected'
    approval_date = db.Column(db.DateTime)

    # Relationship to FoodDistributor
    distributor = db.relationship('FoodDistributor', backref='distribution_requests')


class FoodShelter(db.Model):
    __tablename__ = 'food_shelters'

    shelter_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    contact_number = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)
    status = db.Column(db.String(20), default='pending')

    # Relationship to ShelterOrder
    shelter_orders = db.relationship('ShelterOrder', back_populates='shelter', lazy=True)


class ShelterOrder(db.Model):
    __tablename__ = 'shelter_orders'
    order_id = db.Column(db.Integer, primary_key=True)
    shelter_id = db.Column(db.Integer, db.ForeignKey('food_shelters.shelter_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.item_id'), nullable=False)
    surplus_id = db.Column(db.Integer, db.ForeignKey('surplus_food.surplus_id'), nullable=True)  # Foreign key reference to SurplusFood

    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    shelter = db.relationship('FoodShelter', back_populates='shelter_orders')
    item = db.relationship("Item", back_populates="shelter_orders")
    surplus_food = db.relationship('SurplusFood', back_populates='orders')  # This should now work as expected


class SurplusFood(db.Model):
    __tablename__ = 'surplus_food'
    surplus_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('admin_items.item_id'), nullable=False)  # Ensure it references 'items.item_id'
    quantity = db.Column(db.Integer, nullable=False)
    distributor_id = db.Column(db.Integer, db.ForeignKey('food_distributors.distributor_id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)  #/ e.g., 'pending', 'approved', 'rejected'
    date_added = db.Column(db.DateTime, default=db.func.now())

    # Relationships
    item = db.relationship('AdminItem', backref='surplus_food')  # Add relationship to Item
    distributor = db.relationship('FoodDistributor', backref='surplus_food')
    orders = db.relationship('ShelterOrder', back_populates='surplus_food')

class Order(db.Model):
    __tablename__ = 'orders'

    order_id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.farmer_id'), nullable=False)
    distributor_id = db.Column(db.Integer, db.ForeignKey('food_distributors.distributor_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.item_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, nullable=False)
    payment_status = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    farmer = db.relationship('Farmer', back_populates='orders')
    distributor = db.relationship('FoodDistributor', back_populates='orders')  # Corrected reference
    item = db.relationship('Item')
    order_items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.item_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # Relationships
    order = db.relationship('Order', back_populates='order_items')
    item = db.relationship('Item', back_populates='order_items')


class Item(db.Model):
    __tablename__ = 'items'
    item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    market_price = db.Column(db.Float, nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.farmer_id'), nullable=False)

    # Relationships
    farmer = db.relationship('Farmer', back_populates='items')
    order_items = db.relationship('OrderItem', back_populates='item')
    shelter_orders = db.relationship('ShelterOrder', back_populates='item')

class Cart(db.Model):
    __tablename__ = 'cart'

    cart_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.item_id'), nullable=False)
    distributor_id = db.Column(db.Integer, db.ForeignKey('food_distributors.distributor_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # Relationships
    item = db.relationship('Item', backref='cart_items')
    distributor = db.relationship('FoodDistributor', backref='cart_items')

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(50), nullable=False)  # "Farmer", "Distributor", "Shelter"
    text = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)

@app.route('/register', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])  # Hash the password
        contact_number = request.form['contact_number']
        location = request.form.get('location')
        user_type = request.form['user_type']

        # Check if the username or email already exists for any type of user
        if Farmer.query.filter_by(username=username).first() or \
           FoodDistributor.query.filter_by(username=username).first() or \
           FoodShelter.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for('registration'))

        # Farmer registration
        if user_type == 'farmer':
            new_farmer = Farmer(username=username, email=email, password=password,
                                contact_number=contact_number, location=location)
            db.session.add(new_farmer)

        # Food Distributor registration
        if user_type == 'food_distributor':
            # Debugging point: Print before committing the food distributor
            print(f"Attempting to register food distributor: {username}")
            new_food_distributor = FoodDistributor(
                username=username, email=email, password=password,
                contact_number=contact_number, location=location, status='pending'
            )
            db.session.add(new_food_distributor)

        # Food Shelter registration
        elif user_type == 'food_shelter':
            new_food_shelter = FoodShelter(username=username, email=email, password=password,
                                           contact_number=contact_number, location=location)
            db.session.add(new_food_shelter)

        try:
            db.session.commit()
            flash("Registration successful! Please wait for admin approval.", "success")
            return redirect(url_for('login'))  # Redirect to login after successful registration
        except Exception as e:
            db.session.rollback()  # Rollback on failure
            flash(f"Registration failed: {str(e)}", "danger")
            return redirect(url_for('registration'))

    return render_template('registration.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']  # Get user type from the form

        # Check for farmer
        if user_type == 'farmer':
            farmer = Farmer.query.filter_by(username=username).first()
            if farmer and check_password_hash(farmer.password, password):
                if farmer.status == 'approved':
                    session['farmer_id'] = farmer.farmer_id
                    return redirect(url_for('farmer_dashboard'))
                else:
                    flash("Your account is pending approval.", "warning")
                    return redirect(url_for('login'))
            else:
                flash("Invalid username or password.", "danger")
                return redirect(url_for('login'))
        # Check for food distributor
        # Check for food distributor login
        if user_type == 'food_distributor':
            distributor = FoodDistributor.query.filter_by(username=username).first()

            if distributor:
                # Print distributor details for debugging
                print(f"Distributor found: {distributor.username}, Status: {distributor.status}")

                # Check password hash
                if check_password_hash(distributor.password, password):
                    print("Password correct.")

                    if distributor.status == 'approved':
                        session['distributor_id'] = distributor.distributor_id

                        flash("Login successful!", "success")
                        return redirect(url_for('food_distributor_dashboard'))  # Distributor dashboard
                    else:
                        flash("Your account is pending approval.", "warning")
                        return redirect(url_for('login'))
                else:
                    flash("Incorrect password.", "danger")
                    print("Incorrect password.")
                    return redirect(url_for('login'))
            else:
                flash("Distributor not found.", "danger")
                print("Distributor not found in the database.")
                return redirect(url_for('login'))

        # Check for food shelter
        elif user_type == 'food_shelter':
            shelter = FoodShelter.query.filter_by(username=username).first()
            if shelter and check_password_hash(shelter.password, password):
                if shelter.status == 'approved':
                    session['shelter_id'] = shelter.shelter_id
                    return redirect(url_for('shelter_dashboard'))
                else:
                    flash("Your account is pending approval.", "warning")
                    return redirect(url_for('login'))
            else:
                flash("Invalid username or password.", "danger")
                return redirect(url_for('login'))

        elif user_type == 'admin':
            admin = Admin.query.filter_by(username=username).first()
            if admin and check_password_hash(admin.password, password):
                session['admin_id'] = admin.admin_id
                return redirect(url_for('admin_dashboard'))


        flash("Invalid username or password!", "danger")
        return redirect(url_for('login'))

    return render_template('login.html')
# Admin dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')
@app.route('/admin/manage_items', methods=['GET', 'POST'])
def manage_items():
    # Fetch all items in the AdminItem table (approved items)
    admin_items = AdminItem.query.all()

    # Fetch all pending items that need approval (use pending table)
    pending_items = PendingItem.query.all()

    if request.method == 'POST':
        # Check if the request is for updating an existing item's price
        item_id = request.form.get('item_id')
        market_price = request.form.get('market_price')

        if item_id:
            admin_item = AdminItem.query.get(item_id)  # Fetch the item by ID
            if admin_item:
                admin_item.market_price = market_price  # Update the price
                db.session.commit()  # Commit the changes
                flash('Market price updated successfully!', 'success')
            else:
                flash('Admin item not found', 'error')

        # Handling admin's item approval and price setting
        pending_item_id = request.form.get('pending_item_id')

        if pending_item_id:
            pending_item = PendingItem.query.get(pending_item_id)
            if pending_item:
                # Add to AdminItem table and delete from PendingItem
                new_item = AdminItem(
                    item_name=pending_item.item_name,
                    market_price=market_price
                )
                db.session.add(new_item)
                db.session.delete(pending_item)
                db.session.commit()
                flash('Item approved and added to AdminItem!', 'success')
            else:
                flash('Pending item not found', 'error')

        return redirect(url_for('manage_items'))

    return render_template('manage_items.html', admin_items=admin_items, pending_items=pending_items)

@app.route('/admin/view_farmers', methods=['GET', 'POST'])
def view_farmers():
    if request.method == 'POST':
        farmer_id = request.form.get('shelter_id')  # Change this to match the field name
        action = request.form.get('action')

        farmer = Farmer.query.get_or_404(farmer_id)

        if action == 'approve':
            farmer.status = 'approved'
        elif action == 'reject':
            farmer.status = 'rejected'
            # Optionally delete the farmer from the database:
            # db.session.delete(farmer)

        db.session.commit()
        flash(f"Farmer {farmer.username} has been {action}d successfully!", "success")

    pending_farmers = Farmer.query.filter_by(status='pending').all()
    approved_farmers = Farmer.query.filter_by(status='approved').all()

    return render_template('view_farmers.html', pending_farmers=pending_farmers, approved_farmers=approved_farmers)


@app.route('/admin/approve_farmer/<int:farmer_id>', methods=['POST'])
def approve_farmer(farmer_id):
    # Fetch the farmer by ID
    farmer = Farmer.query.get_or_404(farmer_id)

    if request.method == 'POST':
        action = request.form['action']

        if action == 'approve':
            farmer.status = 'approved'
            flash(f"Farmer {farmer.username} has been approved.", "success")
        elif action == 'reject':
            farmer.status = 'rejected'
            db.session.delete(farmer)  # Remove the farmer from the database
            flash(f"Farmer {farmer.username} has been rejected.", "danger")

        db.session.commit()

    return redirect(url_for('view_farmers'))


@app.route('/admin/view_distribution_teams', methods=['GET', 'POST'])
def view_distribution_teams():
    if request.method == 'POST':
        distributor_id = request.form['distributor_id']
        action = request.form['action']

        distributor = FoodDistributor.query.get(distributor_id)

        if distributor:
            if action == 'approve':
                distributor.status = 'approved'
                flash(f"Food Distributor {distributor.username} has been approved.", "success")
            elif action == 'reject':
                db.session.delete(distributor)
                flash(f"Food Distributor {distributor.username} has been rejected and removed.", "danger")

            db.session.commit()

    # Fetch pending and approved distributors
    pending_distributors = FoodDistributor.query.filter_by(status='pending').all()
    approved_distributors = FoodDistributor.query.filter_by(status='approved').all()

    # Debugging - print the approved distributors to the console
    print(f"Approved Distributors: {approved_distributors}")

    return render_template('view_distribution_teams.html',
                           pending_distributors=pending_distributors,
                           approved_distributors=approved_distributors)


@app.route('/admin/approve_distributor', methods=['GET', 'POST'])
def approve_distributor():
    if request.method == 'POST':
        distributor_id = request.form['distributor_id']
        action = request.form['action']

        distributor = FoodDistributor.query.get(distributor_id)

        if distributor:
            if action == 'approve':
                distributor.status = 'approved'
            elif action == 'reject':
                # If rejecting, delete the distributor from the table
                db.session.delete(distributor)

            db.session.commit()
            flash(f"Food Distributor {distributor.username} has been {action}ed.", "success")

    # Fetch distributors with a pending status
    pending_distributors = FoodDistributor.query.filter_by(status='pending').all()
    approved_distributors = FoodDistributor.query.filter_by(status='approved').all()
    return render_template('view_distribution_teams.html',
                           pending_distributors=pending_distributors,
                           approved_distributors=approved_distributors)


@app.route('/admin/view_food_shelters', methods=['GET', 'POST'])
def view_food_shelters():
    if request.method == 'POST':
        shelter_id = request.form.get('shelter_id')
        action = request.form.get('action')

        shelter = FoodShelter.query.get(shelter_id)

        if shelter:
            if action == 'approve':
                shelter.status = 'approved'
            elif action == 'reject':
                shelter.status = 'rejected'

            db.session.commit()
            flash(f"Food Shelter {shelter.username} has been {action}ed.", "success")

            # Optionally: If rejected, delete the record
            if action == 'reject':
                db.session.delete(shelter)
                db.session.commit()
                flash(f"Food Shelter {shelter.username} has been deleted.", "success")

    # Fetch both pending and approved shelters
    pending_shelters = FoodShelter.query.filter_by(status='pending').all()
    approved_shelters = FoodShelter.query.filter_by(status='approved').all()

    return render_template('view_food_shelters.html', pending_shelters=pending_shelters, approved_shelters=approved_shelters)


@app.route('/admin/approve_food_shelter', methods=['POST'])
def approve_food_shelter():
    shelter_id = request.form['shelter_id']
    action = request.form['action']

    shelter = FoodShelter.query.get(shelter_id)

    if shelter:
        if action == 'approve':
            shelter.status = 'approved'
        elif action == 'reject':
            # Handle reject, either delete or change status
            db.session.delete(shelter)

        db.session.commit()
        flash(f"Food Shelter {shelter.name} has been {action}ed.", "success")

    return redirect(url_for('view_food_shelters'))


@app.route('/admin/view_complaints', methods=['GET'])
def view_complaints():
    complaints = Complaint.query.all()
    return render_template('view_complaints.html', complaints=complaints)


@app.route('/admin/respond_complaint/<int:complaint_id>', methods=['POST'])
def respond_complaint(complaint_id):
    complaint = Complaint.query.get(complaint_id)
    if not complaint:
        flash("Complaint not found!", "error")
        return redirect(url_for('view_complaints'))

    # Update the complaint with the admin's response
    complaint.response = request.form['response']
    db.session.commit()
    flash("Response submitted successfully!", "success")
    return redirect(url_for('view_complaints'))


from sqlalchemy import func
from flask import render_template

@app.route('/admin/view_surplus_usage_report', methods=['GET'])
def view_surplus_usage_report():
    # Calculate total quantity of each item added to surplus
    total_surplus_quantities = (
        db.session.query(SurplusFood.item_id, func.sum(SurplusFood.quantity).label('total_quantity'))
        .group_by(SurplusFood.item_id)
        .all()
    )

    # Calculate total used quantity of each item from approved ShelterOrder
    used_quantities = (
        db.session.query(ShelterOrder.item_id, func.sum(ShelterOrder.quantity).label('used_quantity'))
        .filter(ShelterOrder.status == 'approved')
        .group_by(ShelterOrder.item_id)
        .all()
    )

    # Convert query results to dictionaries for easy lookup
    total_surplus_dict = {item_id: total for item_id, total in total_surplus_quantities}
    used_quantity_dict = {item_id: used for item_id, used in used_quantities}

    # Prepare the report data with item details
    usage_reports = []
    for item_id, total_quantity in total_surplus_dict.items():
        item = AdminItem.query.get(item_id)  # Get item name from AdminItem table

        # Default used quantity to 0 if not present in used_quantity_dict
        used_quantity = used_quantity_dict.get(item_id, 0)

        if item:
            remaining_quantity = total_quantity - used_quantity  # Calculate remaining quantity
            usage_reports.append({
                "item_name": item.item_name,
                "total_quantity": total_quantity,
                "used_quantity": used_quantity,
                "remaining_quantity": remaining_quantity
            })

    return render_template('view_surplus_usage_report.html', usage_reports=usage_reports)


@app.route('/admin/change_password', methods=['GET', 'POST'])
def change_admin_password():
    if request.method == 'POST':
        username = request.form.get('username')
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')

        print(f"Received: username={username}, old_password={old_password}, new_password={new_password}")  # Debugging output

        # Fetch the admin based on username
        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, old_password):  # Check the old password
            admin.password = generate_password_hash(new_password)  # Hash the new password
            db.session.commit()  # Commit the change
            flash("Password changed successfully!", "success")
            return redirect(url_for('admin_dashboard'))  # Redirect to a relevant page
        else:
            flash("Invalid username or password!", "error")

    return render_template('change_password.html')  # Render the password change form

@app.route('/farmer/dashboard', methods=['GET', 'POST'])
def farmer_dashboard():
    if 'farmer_id' not in session:
        return redirect(url_for('login'))

    farmer_id = session['farmer_id']
    farmer = Farmer.query.get(farmer_id)

    # Fetch farmer's items and orders
    items = Item.query.filter_by(farmer_id=farmer_id).all()
    orders = Order.query.filter_by(farmer_id=farmer_id).all()

    if request.method == 'POST':
        # Handle any form submissions if needed
        pass

    return render_template('farmers_dashboard.html', farmer=farmer, items=items, orders=orders)


@app.route('/admin/farmers_update_profile/<int:farmer_id>', methods=['GET', 'POST'])
def farmers_update_profile(farmer_id):
    # Fetch the farmer by ID
    farmer = Farmer.query.get(farmer_id)
    if not farmer:
        flash("Farmer not found!", "danger")
        return redirect(url_for('farmer_dashboard'))

    if request.method == 'POST':
        # Update farmer details
        farmer.username = request.form['username']
        farmer.email = request.form['email']
        farmer.contact_number = request.form.get('contact_number', farmer.contact_number)
        farmer.location = request.form.get('location', farmer.location)

        # Check if a new password was provided
        new_password = request.form.get('password')
        if new_password:  # Only update if a new password is entered
            farmer.password = generate_password_hash(new_password)

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('farmer_dashboard'))

    return render_template('farmers_update_profile.html', farmer=farmer)
@app.route('/farmer/update_stock', methods=['GET', 'POST'])
def farmers_manage_stock():
    farmer_id = session.get('farmer_id')

    if not farmer_id:
        flash("You need to log in as a farmer to manage stock.", "error")
        return redirect(url_for('login'))

    # Fetch all approved items from AdminItem table
    admin_items = AdminItem.query.all()

    # Fetch all items added by the farmer
    farmer_items = Item.query.filter_by(farmer_id=farmer_id).all()

    if request.method == 'POST':
        admin_item_id = request.form.get('admin_item_id')
        new_item_name = request.form.get('item_name')
        stock = request.form.get('stock')

        # Farmer selects an approved item from AdminItem table
        if admin_item_id:
            selected_admin_item = AdminItem.query.get(admin_item_id)
            if selected_admin_item:
                farmer_item = Item.query.filter_by(farmer_id=farmer_id, item_name=selected_admin_item.item_name).first()
                if farmer_item:
                    farmer_item.stock = stock
                    db.session.commit()
                    flash(f'Stock for "{selected_admin_item.item_name}" updated successfully!', 'success')
                else:
                    new_farm_item = Item(
                        item_name=selected_admin_item.item_name,
                        stock=stock,
                        market_price=selected_admin_item.market_price,
                        farmer_id=farmer_id
                    )
                    db.session.add(new_farm_item)
                    db.session.commit()
                    flash(f'New stock for "{selected_admin_item.item_name}" added successfully!', 'success')
            return redirect(url_for('farmers_manage_stock'))

        # Farmer adds a new item for admin approval (no stock needed)
        elif new_item_name:
            existing_admin_item = AdminItem.query.filter_by(item_name=new_item_name).first()
            existing_pending_item = PendingItem.query.filter_by(item_name=new_item_name).first()

            if existing_admin_item:
                flash(f'Item "{new_item_name}" is already approved and available for selection.', 'error')
            elif existing_pending_item:
                flash(f'Item "{new_item_name}" is already submitted for approval.', 'error')
            else:
                # Insert the new item into the PendingItem table without stock
                pending_item = PendingItem(
                    item_name=new_item_name,
                    farmer_id=farmer_id,
                    stock=0
                )
                db.session.add(pending_item)
                db.session.commit()
                flash('New item submitted for admin approval!', 'success')

            return redirect(url_for('farmers_manage_stock'))

    return render_template('farmers_manage_stock.html', admin_items=admin_items, items=farmer_items)

def farmer_items():
    farmer_id = session.get('farmer_id')  # Assume farmer is logged in

    if not farmer_id:
        flash("Please log in as a farmer.", "error")
        return redirect(url_for('login'))

    # Fetch items the farmer has sent for approval and that were added to the AdminItem table
    approved_items = Item.query.filter_by(farmer_id=farmer_id).all()

    return render_template('farmer_manage_items.html', approved_items=approved_items)


@app.route('/farmers/view_orders', methods=['GET', 'POST'])
def farmers_view_orders():
    if request.method == 'POST':
        action = request.form.get('action')
        order_id = request.form.get('order_id')
        order = Order.query.get(order_id)
        if order:
            if action == 'approve':
                order.status = 'approved'
                sufficient_stock = True
                item = Item.query.get(order.item_id)  # Directly fetch item from Item table
                if item and item.stock >= order.quantity:
                    # Reduce the stock
                    item.stock -= order.quantity
                    if item.stock == 0:
                        db.session.delete(item)  # Remove the item if stock becomes zero
                    order.payment_status = 'unpaid'
                    flash(f"Order {order.order_id} approved successfully!", "success")
                    db.session.commit()
                else:
                    sufficient_stock = False
                    flash(f"Insufficient stock for {item.item_name}. Order approval failed.", "danger")
            elif action == 'reject':
                order.status = 'rejected'
                flash(f"Order {order.order_id} rejected.", "danger")
                db.session.commit()
            elif action == 'mark_paid':
                if order.status == 'approved' and order.payment_status == 'unpaid':
                    order.payment_status = 'paid'
                    flash(f"Order {order.order_id} marked as paid successfully!", "success")
                    db.session.commit()
    pending_orders = Order.query.filter_by(status='pending').all()
    approved_orders = Order.query.filter_by(status='approved').all()
    return render_template('farmers_view_orders.html', pending_orders=pending_orders, approved_orders=approved_orders)


@app.route('/delete_order', methods=['POST'])
def delete_order():
    order_id = request.form.get('order_id')
    order = Order.query.get(order_id)

    if order:
        db.session.delete(order)
        db.session.commit()
        flash(f"Order {order_id} deleted successfully!", "success")
    else:
        flash(f"Order {order_id} not found.", "danger")

    return redirect(url_for('farmers_view_orders'))


@app.route('/farmer/farmers_view_complaints', methods=['GET', 'POST'])
def farmers_view_complaints():
    # Logic to handle complaints
    return render_template('farmers_view_complaints.html')

@app.route('/food_distributor/dashboard', methods=['GET', 'POST'])
def food_distributor_dashboard():
    if 'distributor_id' not in session:
        return redirect(url_for('login'))

    distributor_id = session['distributor_id']
    distributor = FoodDistributor.query.get(distributor_id)

    # Fetch items (no distributor_id filtering)
    items = Item.query.all()  # Retrieve all items available in the system

    # Fetch surplus items (you may want to adjust this logic)
    surplus_items = SurplusFood.query.all()  # Retrieve all surplus food items

    return render_template(
        'food_distributor_dashboard.html',
        distributor=distributor,
        items=items,
        surplus_items=surplus_items
    )

@app.route('/admin/distributor_update_profile/<int:distributor_id>', methods=['GET', 'POST'])
def distributor_update_profile(distributor_id):
    distributor = FoodDistributor.query.get(distributor_id)
    if not distributor:
        flash("Distributor not found!", "danger")
        return redirect(url_for('food_distributor_dashboard'))  # Redirect if distributor not found

    if request.method == 'POST':
        # Update distributor's details
        distributor.username = request.form['username']
        distributor.email = request.form['email']
        distributor.contact_number = request.form.get('contact_number', distributor.contact_number)
        distributor.location = request.form.get('location', distributor.location)

        # Optional password change
        new_password = request.form.get('password')
        if new_password:  # Only update if a new password is entered
            distributor.password = generate_password_hash(new_password)

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('food_distributor_dashboard'))

    return render_template('distributor_update_profile.html', distributor=distributor)

@app.route('/search_market', methods=['GET', 'POST'])
def search_market():
    search_results = []
    if request.method == 'POST':
        item_name = request.form.get('item_name')
        query = Item.query.join(Farmer).filter(Item.stock > 0)
        if item_name:
            query = query.filter(Item.item_name.ilike(f'%{item_name}%'))
        search_results = query.all()
    else:
        search_results = Item.query.join(Farmer).filter(Item.stock > 0).all()
    return render_template('search_market.html', search_results=search_results)

@app.route('/distributor/cart', methods=['GET'])
def cart_items():
    distributor_id = session.get('distributor_id')

    if not distributor_id:
        return redirect(url_for('login'))

    # Fetch orders for the current distributor
    orders = Order.query.filter_by(distributor_id=distributor_id).all()

    return render_template('cart.html', orders=orders)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item_id = request.form.get('item_id')
    distributor_id = session.get('distributor_id')  # Fetch distributor_id from session
    quantity = request.form.get('quantity')

    if not distributor_id:
        flash('Distributor not logged in.', 'danger')
        return redirect(url_for('login'))  # Redirect if not logged in

    if not quantity or not quantity.isdigit():
        flash('Invalid quantity.', 'danger')
        return redirect(url_for('search_market'))

    quantity = int(quantity)

    item = Item.query.get(item_id)
    if item and quantity > 0:
        # Create a new Order
        order = Order(
            item_id=item.item_id,
            distributor_id=distributor_id,
            farmer_id=item.farmer_id,
            quantity=quantity,
            status='pending',
            payment_status='unpaid'
        )
        db.session.add(order)
        db.session.commit()

        flash('Item added to cart.', 'success')
    else:
        flash('Failed to add item to cart.', 'danger')

    return redirect(url_for('cart_items'))

def add_to_distributor_items():
    if 'distributor_id' not in session:
        return redirect(url_for('login'))  # Ensure the distributor is logged in

    distributor_id = session['distributor_id']
    item_id = request.form.get('item_id')

    # Fetch the item from the Item table
    item = Item.query.get(item_id)

    if not item:
        flash('Item not found.', 'danger')
        return redirect(url_for('search_market'))

    # Check if the item already exists for this distributor
    existing_distributor_item = DistributorItem.query.filter_by(item_id=item_id, distributor_id=distributor_id).first()

    if existing_distributor_item:
        flash('This item is already added to your stock.', 'warning')
    else:
        # Add item to the distributor's stock without the stock field
        new_distributor_item = DistributorItem(
            item_id=item_id,
            item_name=item.item_name,
            distributor_id=distributor_id  # No stock field
        )
        db.session.add(new_distributor_item)
        db.session.commit()
        flash('Item added to your stock successfully!', 'success')

    return redirect(url_for('cart_items'))

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    if 'distributor_id' not in session:
        return redirect(url_for('login'))  # Ensure the distributor is logged in

    # Fetch the order to cancel
    order = Order.query.get(order_id)

    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('cart_items'))

    # Only allow cancellation if the order is still pending
    if order.status == 'pending':
        db.session.delete(order)
        db.session.commit()
        flash('Order has been canceled.', 'success')
    else:
        flash('Only pending orders can be canceled.', 'danger')

    return redirect(url_for('cart_items'))


@app.route('/delete_cart_item/<int:order_id>', methods=['POST'])
def delete_cart_item(order_id):
    order = Order.query.get(order_id)

    if order:
        db.session.delete(order)
        db.session.commit()
        flash(f"Order {order_id} deleted successfully!", "success")
    else:
        flash(f"Order {order_id} not found.", "danger")

    return redirect(url_for('farmers_view_orders'))


@app.route('/approve_order/<int:order_id>', methods=['POST'])
def approve_order(order_id):
    if 'distributor_id' not in session:
        return redirect(url_for('login'))  # Ensure the distributor is logged in

    # Fetch the order to approve
    order = Order.query.get(order_id)

    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('cart_items'))

    # Update order status to approved
    order.status = 'approved'
    db.session.commit()

    # Now add the approved item to the DistributorItem table
    distributor_id = session['distributor_id']
    item_id = order.item_id  # Assuming you have item_id in the order

    # Check if the item already exists for this distributor
    existing_distributor_item = DistributorItem.query.filter_by(item_id=item_id, distributor_id=distributor_id).first()

    if not existing_distributor_item:
        # If not, add the item to the distributor's items
        new_distributor_item = DistributorItem(
            item_id=item_id,
            item_name=order.item.item_name,  # Ensure the name is taken from the order
            distributor_id=distributor_id
        )
        db.session.add(new_distributor_item)
        db.session.commit()
        flash('Item added to your stock successfully!', 'success')
    else:
        flash('Item is already in your stock.', 'warning')

    return redirect(url_for('cart_items'))


@app.route('/distributor/add_surplus', methods=['GET', 'POST'])
def distributor_add_surplus():
    distributor_id = session.get('distributor_id')

    if request.method == 'POST':
        item_id = request.form.get('item_id')
        quantity = request.form.get('quantity')

        # Validate that item_id and quantity are provided
        if not item_id or not quantity:
            flash('Item ID and quantity are required.', 'error')
            return redirect(url_for('distributor_add_surplus'))

        # Convert quantity to integer and validate
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be a positive number.")
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('distributor_add_surplus'))

        # Fetch the existing surplus item for the distributor using both item_id and distributor_id
        surplus_item = SurplusFood.query.filter_by(item_id=item_id, distributor_id=distributor_id).first()

        if surplus_item:
            # If the item exists, update the quantity by adding the new quantity
            surplus_item.quantity += quantity  # Update quantity to include the new addition
            surplus_item.status = 'pending'  # Ensure status is pending if you need to track this
            db.session.commit()
            flash('Surplus item quantity updated successfully!', 'success')
        else:
            # If the item doesn't exist, create a new surplus item
            surplus_item = SurplusFood(
                item_id=item_id,
                quantity=quantity,
                distributor_id=distributor_id,
                status='pending'
            )
            db.session.add(surplus_item)
            db.session.commit()
            flash('New surplus item added successfully!', 'success')

        return redirect(url_for('distributor_add_surplus'))

    # Retrieve all items from AdminItem and current surplus items for the distributor
    available_items = AdminItem.query.all()
    surplus_food = SurplusFood.query.filter_by(distributor_id=distributor_id).all()

    return render_template('distributor_add_surplus.html',
                           available_items=available_items,
                           surplus_food=surplus_food,
                           current_distributor_id=distributor_id)

@app.route('/view_surplus_requests')
def view_surplus_requests():
    # Query for all surplus requests along with associated ordered quantities (if any)
    surplus_requests = db.session.query(
        SurplusFood,
        ShelterOrder.quantity.label('ordered_quantity'),
        Item.item_name,
        ShelterOrder.status.label('order_status')  # Filter by ShelterOrder status
    ).join(Item, SurplusFood.item_id == Item.item_id) \
     .outerjoin(ShelterOrder, SurplusFood.surplus_id == ShelterOrder.surplus_id) \
     .all()

    # Filtering requests based on ShelterOrder status only
    pending_requests = [req for req in surplus_requests if req.order_status == 'pending']
    approved_requests = [req for req in surplus_requests if req.order_status == 'approved']
    rejected_requests = [req for req in surplus_requests if req.order_status == 'rejected']

    # Debugging output for pending requests
    print("Pending Requests:", pending_requests)

    return render_template(
        'view_surplus_requests.html',
        pending_requests=pending_requests,
        approved_requests=approved_requests,
        rejected_requests=rejected_requests
    )

@app.route('/approve_surplus_request/<int:surplus_id>', methods=['POST'])
def approve_surplus_request(surplus_id):
    # Find the surplus request and associated shelter order
    surplus_request = SurplusFood.query.get(surplus_id)

    if not surplus_request:
        flash('Surplus request not found.', 'danger')
        return redirect(url_for('view_surplus_requests'))

    # Find the ShelterOrder associated with this surplus request
    shelter_order = ShelterOrder.query.filter_by(surplus_id=surplus_request.surplus_id).first()

    if shelter_order:
        # Check if surplus quantity is sufficient
        if surplus_request.quantity >= shelter_order.quantity:
            # Approve the order
            shelter_order.status = 'approved'
            # Deduct the ordered quantity from the surplus item
            surplus_request.quantity -= shelter_order.quantity
            db.session.commit()
            flash('Surplus request approved successfully and quantity updated!', 'success')
        else:
            flash('Not enough quantity in surplus to fulfill the order.', 'danger')
            return redirect(url_for('view_surplus_requests'))
    else:
        flash('No associated order found to approve.', 'danger')

    return redirect(url_for('view_surplus_requests'))


@app.route('/reject_surplus_request/<int:surplus_id>', methods=['POST'])
def reject_surplus_request(surplus_id):
    surplus_request = SurplusFood.query.get(surplus_id)

    if not surplus_request:
        flash('Surplus request not found.', 'danger')
        return redirect(url_for('view_surplus_requests'))

    # Find associated ShelterOrder
    shelter_order = ShelterOrder.query.filter_by(surplus_id=surplus_request.surplus_id).first()

    if shelter_order:
        shelter_order.status = 'rejected'
        db.session.commit()
        flash('Surplus request rejected successfully!', 'success')
    else:
        flash('No associated order found to reject.', 'danger')

    return redirect(url_for('view_surplus_requests'))

@app.route('/food_shelter/dashboard', methods=['GET', 'POST'])
def shelter_dashboard():
    if 'shelter_id' not in session:
        flash("You must be logged in to access the dashboard.", "warning")
        return redirect(url_for('login'))

    shelter_id = session['shelter_id']
    shelter = FoodShelter.query.get(shelter_id)

    # Check if the shelter exists
    if not shelter:
        flash("Shelter not found. Please contact the administrator.", "danger")
        return redirect(url_for('login'))

    # Fetch surplus items and previous orders
    surplus_items = DistributorItem.query.all()
    previous_orders = ShelterOrder.query.filter_by(shelter_id=shelter_id).all()

    # Optional: Add logic to handle POST requests if needed
    if request.method == 'POST':
        # Handle form submission or any actions from the dashboard
        # For example, processing an order or submitting a request
        pass

    return render_template('shelter_dashboard.html', shelter=shelter, surplus_items=surplus_items, previous_orders=previous_orders)


@app.route('/admin/shelter_update_profile/<int:shelter_id>', methods=['GET', 'POST'])
def shelter_update_profile(shelter_id):
    shelter = FoodShelter.query.get(shelter_id)
    if not shelter:
        flash("Shelter not found!", "danger")
        return redirect(url_for('shelter_dashboard'))  # Redirect if shelter not found

    if request.method == 'POST':
        # Update shelter details
        shelter.username = request.form['username']
        shelter.email = request.form['email']
        shelter.contact_number = request.form.get('contact_number', shelter.contact_number)
        shelter.location = request.form.get('location', shelter.location)

        # Check for a new password
        new_password = request.form.get('password')
        if new_password:  # Only update if a new password is entered
            shelter.password = generate_password_hash(new_password)

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('shelter_dashboard'))

    return render_template('shelter_update_profile.html', shelter=shelter)

@app.route('/view_and_order_surplus_items/<int:shelter_id>', methods=['GET', 'POST'])
def view_and_order_surplus_items(shelter_id):
    if request.method == 'POST':
        # Handle the ordering process here
        item_id = request.form.get('item_id')
        surplus_id = request.form.get('surplus_id')
        quantity = int(request.form.get('quantity', 0))

        # Retrieve the surplus item
        surplus_item = SurplusFood.query.get(surplus_id)

        # Validate the surplus item and the quantity
        if surplus_item and surplus_item.quantity >= quantity > 0:
            # Create a new order
            new_order = ShelterOrder(
                shelter_id=shelter_id,
                item_id=item_id,
                surplus_id=surplus_id,
                quantity=quantity,
                status='pending'  # Order is pending approval
            )
            try:
                db.session.add(new_order)
                db.session.commit()
                flash('Order placed successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error placing order: {e}', 'error')
        else:
            flash('Invalid quantity or surplus item not found.', 'error')

        return redirect(url_for('view_and_order_surplus_items', shelter_id=shelter_id))

    # Query to fetch surplus items with associated item names, only those with positive total quantities
    surplus_items = db.session.query(
        SurplusFood.surplus_id,
        SurplusFood.item_id,
        Item.item_name,
        db.func.sum(SurplusFood.quantity).label('total_quantity')
    ).join(Item, SurplusFood.item_id == Item.item_id) \
     .group_by(SurplusFood.surplus_id, SurplusFood.item_id, Item.item_name) \
     .having(db.func.sum(SurplusFood.quantity) > 0) \
     .all()

    # Debug statement to confirm fetched items
    print("Fetched Surplus Items:", surplus_items)

    return render_template('view_and_order_surplus_items.html', surplus_items=surplus_items, shelter_id=shelter_id)



@app.route('/shelter/view_processed_orders/<int:shelter_id>', methods=['GET'])
def view_processed_orders(shelter_id):
    # Query to get processed orders for the shelter
    processed_orders = (
        db.session.query(ShelterOrder)
        .join(SurplusFood, ShelterOrder.surplus_id == SurplusFood.surplus_id)
        .join(Item, SurplusFood.item_id == Item.item_id)
        .add_columns(Item.item_name, SurplusFood.quantity)
        .filter(
            ShelterOrder.shelter_id == shelter_id,
            ShelterOrder.status.in_(['approved', 'rejected', 'pending'])
        )
        .all()
    )

    # Log the processed orders for debugging
    app.logger.debug(f'Processed Orders: {processed_orders}')

    # Render the template with the processed orders
    return render_template('view_processed_orders.html', processed_orders=processed_orders)
@app.route('/shelter/delete_order/<int:order_id>', methods=['POST'])
def shelter_delete_order(order_id):
    order = ShelterOrder.query.get(order_id)
    if order and order.status in ['approved', 'rejected']:
        db.session.delete(order)
        db.session.commit()
        flash('Order deleted successfully.', 'success')
    else:
        flash('Order cannot be deleted.', 'error')
    return redirect(url_for('view_processed_orders', shelter_id=order.shelter_id))

@app.route('/shelter/cancel_order/<int:order_id>', methods=['POST'])
def shelter_cancel_order(order_id):
    order = ShelterOrder.query.get(order_id)
    if order and order.status == 'pending':
        db.session.delete(order)
        db.session.commit()
        flash('Order canceled successfully.', 'success')
    else:
        flash('Order cannot be canceled.', 'error')
    return redirect(url_for('view_processed_orders', shelter_id=order.shelter_id))
# Route for Farmer to submit a complaint
@app.route('/farmer/submit_complaint', methods=['GET', 'POST'])
def farmer_submit_complaint():
    user_id = session.get('farmer_id')  # Get distributor's ID from the session
    print(f"Session Distributor ID: {user_id}")  # Debugging line

    if request.method == 'POST':
        text = request.form['text']

        if user_id is not None:  # Ensure user_id is available
            complaint = Complaint(user_id=user_id, user_type="Farmer", text=text)
            try:
                db.session.add(complaint)
                db.session.commit()
                flash("Complaint submitted successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred while submitting your complaint: {str(e)}", "danger")
        else:
            flash("User ID not found. Please log in again.", "danger")

    complaints = Complaint.query.filter_by(user_id=user_id, user_type="Farmer").all()
    return render_template('submit_complaint.html', user_type="Farmer", complaints=complaints)


@app.route('/distributor/submit_complaint', methods=['GET', 'POST'])
def distributor_submit_complaint():
    user_id = session.get('distributor_id')  # Get distributor's ID from the session
    print(f"Session Distributor ID: {user_id}")  # Debugging line

    if request.method == 'POST':
        text = request.form['text']

        if user_id is not None:  # Ensure user_id is available
            complaint = Complaint(user_id=user_id, user_type="Distributor", text=text)
            try:
                db.session.add(complaint)
                db.session.commit()
                flash("Complaint submitted successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred while submitting your complaint: {str(e)}", "danger")
        else:
            flash("User ID not found. Please log in again.", "danger")

    complaints = Complaint.query.filter_by(user_id=user_id, user_type="Distributor").all()
    return render_template('distributor_submit_complaint.html', user_type="Distributor", complaints=complaints)


# Route for Shelter to submit a complaint
@app.route('/shelter/submit_complaint', methods=['GET', 'POST'])
def shelter_submit_complaint():
    user_id = session.get('shelter_id')  # Get distributor's ID from the session
    print(f"Session Distributor ID: {user_id}")  # Debugging line

    if request.method == 'POST':
        text = request.form['text']

        if user_id is not None:  # Ensure user_id is available
            complaint = Complaint(user_id=user_id, user_type="Shelter", text=text)
            try:
                db.session.add(complaint)
                db.session.commit()
                flash("Complaint submitted successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred while submitting your complaint: {str(e)}", "danger")
        else:
            flash("User ID not found. Please log in again.", "danger")

    complaints = Complaint.query.filter_by(user_id=user_id, user_type="Shelter").all()
    return render_template('shelter_submit_complaint.html', user_type="Distributor", complaints=complaints)


@app.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        try:
            # Create all tables based on models
            print("Creating tables...")
            db.create_all()
            print("Tables created successfully")
        except Exception as e:
            # Rollback in case of error
            db.session.rollback()
            print(f"An error occurred: {str(e)}")

    app.run(debug=True)  # Run the Flask app

# def add_admin(username, plain_text_password="123456"):
#     with app.app_context():  # Enter application context
#         # Hash the password before storing
#         hashed_password = generate_password_hash(plain_text_password)
#
#         # Create a new admin object
#         new_admin = Admin(username=username, password=hashed_password)
#
#         try:
#             # Add the new admin to the session and commit to the database
#             db.session.add(new_admin)
#             db.session.commit()
#             print("Admin added successfully!")
#         except Exception as e:
#             db.session.rollback()
#             print(f"Failed to add admin: {e}")
#
#
# # Example: Call the function to add a new admin with username "admin" and password "123456"
# add_admin("admin", "123456")
