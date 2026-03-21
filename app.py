cd ~/njoro-kitchen-flask

# Backup your current app.py
cp app.py app.py.backup

# Create a clean app.py with SQLite ONLY
cat > app.py << 'EOF'
from flask import Flask, render_template, session, redirect, url_for, request, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets
import json
import os
import base64
import requests
from requests.auth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'njoro-kitchen-secret-key-2026'

# FORCE SQLITE - USE /tmp (writable on Render)
import os
db_path = os.path.join('/tmp', 'njoro_kitchen.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============================================
# M-PESA CONFIGURATION
# ============================================
MPESA_CONSUMER_KEY = '04E8hdIE1fmT3WaZKHVZ1c1qhKspIjXbdAxaa28WXjOhZaZ9'
MPESA_CONSUMER_SECRET = 'AXKZrLHrxzCPLiTV2hjphr2LOD0tyegG1Id69qwdFDuLFEmGc6xG0VI0a0v568RG'
MPESA_PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
MPESA_SHORTCODE = '174379'
MPESA_CALLBACK_URL = 'https://your-ngrok-id.ngrok-free.dev/mpesa-callback'

# ============================================
# DATABASE MODELS
# ============================================

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(255))
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    category = db.Column(db.String(20))
    prep_time = db.Column(db.Integer, default=15)
    image_url = db.Column(db.String(255))
    is_available = db.Column(db.Boolean, default=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True)
    table_number = db.Column(db.Integer)
    customer_name = db.Column(db.String(100))
    items = db.Column(db.JSON)
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    payment_status = db.Column(db.String(20), default='unpaid')
    payment_time = db.Column(db.DateTime)
    mpesa_checkout_id = db.Column(db.String(100))
    special_instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

# ============================================
# CREATE DEFAULT ADMIN ON FIRST RUN
# ============================================
def create_default_admin():
    """Create default admin user if no admin exists"""
    with app.app_context():
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@njoro.com',
                full_name='System Administrator',
                role='admin',
                is_active=True
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created successfully!")
            print("✅ Email: admin@njoro.com")
            print("✅ Password: Admin@123")
        else:
            print("✅ Admin already exists")

# ============================================
# M-PESA HELPER FUNCTIONS (MOCK for now)
# ============================================

def get_mpesa_access_token():
    """Mock token for testing"""
    print("✅ Using MOCK access token")
    return "mock_token_12345"

def stk_push(phone_number, amount, order_id):
    """Mock STK push - always succeeds"""
    print(f"\n✅ MOCK PAYMENT: Order #{order_id} - KSh {amount} to {phone_number}")
    return {
        'success': True,
        'checkout_id': f"MOCK_{order_id}",
        'message': 'Payment successful (MOCK)'
    }, 200

# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    role = request.form.get('role')
    
    if role == 'customer':
        session['role'] = 'customer'
        session['table'] = int(request.form.get('table', 1))
        session['customer_name'] = request.form.get('customer_name', 'Guest')
        return redirect(url_for('customer_menu'))
    
    login_id = request.form.get('login_id')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=login_id).first()
    if not user:
        user = User.query.filter_by(username=login_id).first()
    
    if user and user.check_password(password) and user.is_active:
        session['user_id'] = user.id
        session['role'] = user.role
        session['full_name'] = user.full_name
        
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'waiter':
            return redirect(url_for('waiter_dashboard'))
        elif user.role == 'cook':
            return redirect(url_for('cook_dashboard'))
    
    flash('Invalid credentials', 'error')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ============================================
# CUSTOMER ROUTES
# ============================================

@app.route('/menu')
def customer_menu():
    items = MenuItem.query.filter_by(is_available=True).all()
    return render_template('menu.html', 
                         items=items, 
                         table=session.get('table', 1),
                         customer_name=session.get('customer_name', 'Guest'))

@app.route('/api/place-order', methods=['POST'])
def place_order():
    data = request.get_json()
    
    today = datetime.now()
    order_count = Order.query.count()
    order_number = f"ORD-{today.strftime('%Y%m%d')}-{order_count + 1:04d}"
    
    order = Order(
        order_number=order_number,
        table_number=data['table'],
        customer_name=session.get('customer_name', 'Guest'),
        items=data['items'],
        total_amount=data['total']
    )
    
    db.session.add(order)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'order_id': order.id,
        'payment_url': f'/payment/{order.id}'
    })

@app.route('/payment/<int:order_id>')
def payment_page(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('payment.html', order=order)

@app.route('/api/initiate-payment', methods=['POST'])
def initiate_payment():
    data = request.get_json()
    order_id = data.get('order_id')
    phone = data.get('phone')
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'error': 'Order not found'})
    
    # Mock payment - always succeeds
    order.payment_status = 'paid'
    order.payment_time = datetime.utcnow()
    order.status = 'completed'
    db.session.commit()
    
    return jsonify({'success': True}), 200

# ============================================
# WAITER ROUTES
# ============================================

@app.route('/waiter')
def waiter_dashboard():
    if 'role' not in session or session['role'] != 'waiter':
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/api/orders')
def get_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify({'orders': [{
        'id': o.id,
        'order_number': o.order_number,
        'table_number': o.table_number,
        'customer_name': o.customer_name,
        'total_amount': o.total_amount,
        'status': o.status,
        'payment_status': o.payment_status,
        'items': o.items,
        'created_at': o.created_at.isoformat()
    } for o in orders]})

@app.route('/api/update-order-status', methods=['POST'])
def update_order_status():
    data = request.get_json()
    order = Order.query.get(data['order_id'])
    if order:
        order.status = data['status']
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

# ============================================
# KITCHEN & COOK ROUTES
# ============================================

@app.route('/kitchen')
def kitchen_display():
    if 'role' not in session or session['role'] != 'cook':
        return redirect(url_for('index'))
    return render_template('kitchen.html')

@app.route('/cook')
def cook_dashboard():
    if 'role' not in session or session['role'] != 'cook':
        return redirect(url_for('index'))
    return render_template('cook_dashboard.html', now=datetime.now())

@app.route('/api/kitchen-orders')
def get_kitchen_orders():
    orders = Order.query.filter(
        Order.status.in_(['pending', 'preparing'])
    ).order_by(Order.created_at).all()
    return jsonify({'orders': [{
        'id': o.id,
        'order_number': o.order_number,
        'table_number': o.table_number,
        'status': o.status,
        'items': o.items,
        'special_instructions': o.special_instructions,
        'created_at': o.created_at.isoformat()
    } for o in orders]})

# ============================================
# ADMIN ROUTES
# ============================================

@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter_by(payment_status='paid').scalar() or 0
    total_customers = Order.query.distinct(Order.table_number).count()
    total_staff = User.query.filter(User.role.in_(['waiter', 'cook'])).count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    staff = User.query.filter(User.role.in_(['waiter', 'cook', 'admin'])).all()
    
    return render_template('admin_dashboard.html',
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         total_customers=total_customers,
                         total_staff=total_staff,
                         recent_orders=recent_orders,
                         staff=staff,
                         now=datetime.now())

@app.route('/admin/users')
def admin_users():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/add', methods=['POST'])
def admin_add_user():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'success': False, 'error': 'Username exists'})
    
    user = User(
        username=data['username'],
        full_name=data['full_name'],
        email=data.get('email', ''),
        role=data['role'],
        is_active=True
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/menu')
def admin_menu():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    return render_template('admin_menu.html')

@app.route('/admin/inventory')
def admin_inventory():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    return render_template('inventory.html')

@app.route('/admin/reports')
def admin_reports():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    return render_template('reports.html')

@app.route('/admin/settings')
def admin_settings():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    return render_template('settings.html')

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()
        print("✅" + "="*50)
        print("✅ DATABASE READY (SQLite)")
        print("✅ ADMIN: admin@njoro.com / Admin@123")
        print("✅" + "="*50)
    
    app.run(debug=True, port=5000, host='0.0.0.0')
EOF