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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/njoro_kitchen.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============================================
# M-PESA CONFIGURATION - USE YOUR CREDENTIALS
# ============================================

# ============================================
MPESA_CONSUMER_KEY = '04E8hdIE1fmT3WaZKHVZ1c1qhKspIjXbdAxaa28WXjOhZaZ9'
MPESA_CONSUMER_SECRET = 'AXKZrLHrxzCPLiTV2hjphr2LOD0tyegG1Id69qwdFDuLFEmGc6xG0VI0a0v568RG'
MPESA_PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'  # Universal sandbox passkey
MPESA_SHORTCODE = '174379'
MPESA_CALLBACK_URL = 'https://your-ngrok-id.ngrok-free.dev/mpesa-callback'  # Replace with your actual ngrok URL # Update with your ngrok URL'  # Replace with your ngrok URL' # Replace with your ngrok URL

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
# M-PESA HELPER FUNCTIONS
# ============================================

def get_mpesa_access_token():
    """Get OAuth token from Safaricom"""
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    
    try:
        response = requests.get(
            api_url,
            auth=HTTPBasicAuth(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET),
            timeout=30
        )
        
        if response.status_code == 200:
            access_token = response.json().get('access_token')
            print("✅ Access token obtained successfully")
            return access_token
        else:
            print(f"❌ Failed to get token: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting access token: {e}")
        return None

def generate_password():
    """Generate the password for STK push"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = MPESA_SHORTCODE + MPESA_PASSKEY + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode('utf-8')
    return password, timestamp

def stk_push(phone_number, amount, order_id):
    """Send real STK push to customer's phone"""
    access_token = get_mpesa_access_token()
    if not access_token:
        return {'success': False, 'error': 'Failed to get access token'}, 500
    
    password, timestamp = generate_password()
    
    # Format phone number correctly
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif phone_number.startswith('+'):
        phone_number = phone_number[1:]
    elif not phone_number.startswith('254'):
        phone_number = '254' + phone_number
    
    api_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'BusinessShortCode': MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(amount),
        'PartyA': phone_number,
        'PartyB': MPESA_SHORTCODE,
        'PhoneNumber': phone_number,
        'CallBackURL': f'{MPESA_CALLBACK_URL}/{order_id}',
        'AccountReference': f'Order{order_id}',
        'TransactionDesc': f'Payment for Order #{order_id}'
    }
    
    print("\n" + "="*60)
    print(f"🔵 STK PUSH REQUEST - Order #{order_id}")
    print(f"📱 Phone: {phone_number}")
    print(f"💰 Amount: KSh {amount}")
    print(f"🔗 Callback URL: {MPESA_CALLBACK_URL}/{order_id}")
    print("="*60)
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        
        print("\n📥 SAFARICOM RESPONSE:")
        print(json.dumps(result, indent=2))
        
        if result.get('ResponseCode') == '0':
            print(f"\n✅ STK PUSH SENT SUCCESSFULLY!")
            print(f"🔑 CheckoutRequestID: {result.get('CheckoutRequestID')}")
            return {
                'success': True,
                'checkout_id': result.get('CheckoutRequestID'),
                'message': result.get('CustomerMessage', 'STK push sent successfully')
            }, 200
        else:
            print(f"\n❌ STK PUSH FAILED: {result.get('errorMessage', 'Unknown error')}")
            return {
                'success': False,
                'error': result.get('errorMessage', 'Unknown error')
            }, 400
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

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
    
    # For cash/card, just mark as paid
    if phone == 'cash' or phone == 'card':
        order.payment_status = 'paid'
        order.payment_time = datetime.utcnow()
        order.status = 'completed'
        db.session.commit()
        return jsonify({'success': True}), 200
    
    # For M-Pesa, send STK push
    result, status_code = stk_push(phone, order.total_amount, order_id)
    
    if status_code == 200 and result.get('success'):
        order.mpesa_checkout_id = result.get('checkout_id')
        db.session.commit()
    
    return jsonify(result), status_code

@app.route('/mpesa-callback/<int:order_id>', methods=['POST'])
def mpesa_callback(order_id):
    """Handle M-Pesa callback"""
    callback_data = request.json
    
    print("\n" + "📞"*30)
    print("📞 M-PESA CALLBACK RECEIVED")
    print("📞"*30)
    print(json.dumps(callback_data, indent=2))
    
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'ResultCode': 1, 'ResultDesc': 'Order not found'})
        
        if callback_data and 'Body' in callback_data:
            stk_callback = callback_data['Body']['stkCallback']
            result_code = stk_callback.get('ResultCode')
            
            if result_code == 0:
                order.payment_status = 'paid'
                order.payment_time = datetime.utcnow()
                order.status = 'completed'
                db.session.commit()
                print(f"✅ Payment completed for Order #{order_id}")
                return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'})
            else:
                print(f"❌ Payment failed: {stk_callback.get('ResultDesc')}")
                return jsonify({'ResultCode': result_code, 'ResultDesc': stk_callback.get('ResultDesc')})
        
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Invalid callback'})
    
    except Exception as e:
        print(f"❌ Callback error: {str(e)}")
        return jsonify({'ResultCode': 1, 'ResultDesc': str(e)})

@app.route('/api/check-payment-status/<int:order_id>')
def check_payment_status(order_id):
    order = Order.query.get(order_id)
    if order:
        return jsonify({
            'paid': order.payment_status == 'paid',
            'status': order.payment_status
        })
    return jsonify({'paid': False})

@app.route('/order-tracking/<int:order_id>')
def order_tracking(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('order_tracking.html', order=order)

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
# KITCHEN & COOK ROUTES - CORRECTED (NO DUPLICATES)
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
# ADMIN ROUTES - COMPLETE MANAGEMENT
# ============================================

@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    
    # Statistics
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter_by(payment_status='paid').scalar() or 0
    
    # Today's stats
    today = datetime.now().date()
    new_orders_today = Order.query.filter(db.func.date(Order.created_at) == today).count()
    today_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
        db.func.date(Order.created_at) == today,
        Order.payment_status == 'paid'
    ).scalar() or 0
    
    # Customer stats
    total_customers = Order.query.distinct(Order.table_number).count()
    active_customers = Order.query.filter(
        Order.status.in_(['pending', 'preparing', 'ready']),
        db.func.date(Order.created_at) == today
    ).distinct(Order.table_number).count()
    
    # Staff stats
    total_staff = User.query.filter(User.role.in_(['waiter', 'cook'])).count()
    active_staff = User.query.filter(
        User.role.in_(['waiter', 'cook']),
        User.is_active == True
    ).count()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Staff list
    staff = User.query.filter(User.role.in_(['waiter', 'cook', 'admin'])).all()
    
    # Low stock items (if you have inventory)
    low_stock = []  # Add inventory query if you have it
    
    return render_template('admin_dashboard.html',
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         new_orders_today=new_orders_today,
                         today_revenue=today_revenue,
                         total_customers=total_customers,
                         active_customers=active_customers,
                         total_staff=total_staff,
                         active_staff=active_staff,
                         recent_orders=recent_orders,
                         staff=staff,
                         low_stock=low_stock,
                         now=datetime.now())

@app.route('/admin/users')
def admin_users():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/<int:id>')
def admin_get_user(id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'full_name': user.full_name,
        'email': user.email,
        'role': user.role,
        'is_active': user.is_active
    })

@app.route('/admin/user/add', methods=['POST'])
def admin_add_user():
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.get_json()
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'success': False, 'error': 'Username already exists'})
    
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

@app.route('/admin/user/update/<int:id>', methods=['POST'])
def admin_update_user(id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    user = User.query.get_or_404(id)
    data = request.get_json()
    
    user.full_name = data['full_name']
    user.email = data['email']
    user.role = data['role']
    
    if data.get('password'):
        user.set_password(data['password'])
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/user/toggle/<int:id>', methods=['POST'])
def admin_toggle_user(id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/user/delete/<int:id>', methods=['POST'])
def admin_delete_user(id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    user = User.query.get_or_404(id)
    if user.username == 'admin':
        return jsonify({'success': False, 'error': 'Cannot delete main admin account'})
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/orders')
def admin_orders():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_orders.html', orders=orders)

# ============================================
# ADMIN MENU MANAGEMENT
# ============================================

@app.route('/admin/menu')
def admin_menu():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    return render_template('admin_menu.html')

@app.route('/api/menu-items/<int:id>')
def get_menu_item(id):
    item = MenuItem.query.get_or_404(id)
    return jsonify({
        'id': item.id,
        'name': item.name,
        'description': item.description,
        'price': item.price,
        'category': item.category,
        'prep_time': item.prep_time,
        'image_url': item.image_url,
        'is_available': item.is_available
    })

@app.route('/admin/menu/add', methods=['POST'])
def admin_menu_add():
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.get_json()
    item = MenuItem(
        name=data['name'],
        description=data.get('description', ''),
        price=data['price'],
        category=data['category'],
        prep_time=data.get('prep_time', 15),
        image_url=data.get('image_url', ''),
        is_available=True
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/menu/update/<int:id>', methods=['POST'])
def admin_menu_update(id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    item = MenuItem.query.get_or_404(id)
    data = request.get_json()
    
    item.name = data['name']
    item.description = data.get('description', '')
    item.price = data['price']
    item.category = data['category']
    item.prep_time = data.get('prep_time', 15)
    item.image_url = data.get('image_url', '')
    item.is_available = data.get('is_available', True)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/menu/delete/<int:id>', methods=['POST'])
def admin_menu_delete(id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    item = MenuItem.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})

# ============================================
# ADMIN INVENTORY, REPORTS, SETTINGS
# ============================================

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
        print("✅ DATABASE READY")
        print("✅ M-PESA INTEGRATION ACTIVE")
        print("✅ ADMIN LOGIN: admin@njoro.com / Admin@123")
        print("✅ WAITER: Create via admin panel")
        print("✅ COOK: Create via admin panel")
        print("✅" + "="*50)
    
    app.run(debug=True, port=5000, host='0.0.0.0')