from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smart_locker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'active': self.active
        }

class Locker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(10), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available')
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_user_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'status': self.status,
            'assigned_user_id': self.assigned_user_id,
            'assigned_user_name': self.assigned_user_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    locker_id = db.Column(db.Integer, db.ForeignKey('locker.id'))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Login routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Create admin user if not exists
def create_admin_user():
    if not User.query.filter_by(username='serrah').first():
        admin = User(username='serrah', email='serrah@example.com', role='admin')
        admin.set_password('serra123')
        db.session.add(admin)
        db.session.commit()
        create_sample_data()  # Create sample data after admin user is created

# Routes
@app.route('/')
@login_required
def dashboard():
    return render_template('index.html')

@app.route('/api/stats')
@login_required
def get_stats():
    total_users = User.query.count()
    active_lockers = Locker.query.filter_by(status='occupied').count()
    total_lockers = Locker.query.count()
    pending_payments = Payment.query.filter_by(status='pending').count()
    
    return jsonify({
        'users': total_users,
        'active_lockers': active_lockers,
        'total_lockers': total_lockers,
        'pending_payments': pending_payments
    })

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'user')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if current_user.role != 'admin' and current_user.id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'username' in data and data['username'] != user.username:
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        user.username = data['username']
    
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        user.email = data['email']
    
    if 'password' in data:
        user.set_password(data['password'])
    
    if 'role' in data and current_user.role == 'admin':
        user.role = data['role']
    
    db.session.commit()
    return jsonify(user.to_dict())

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    db.session.delete(user)
    db.session.commit()
    return '', 204

@app.route('/api/lockers', methods=['GET'])
@login_required
def get_lockers():
    lockers = Locker.query.all()
    return jsonify([{
        'id': locker.id,
        'number': locker.number,
        'status': locker.status,
        'assigned_user_name': locker.assigned_user_name
    } for locker in lockers])

@app.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    if current_user.role != 'admin' and current_user.id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@app.route('/api/reservations', methods=['GET'])
@login_required
def get_reservations():
    reservations = Reservation.query.all()
    return jsonify([{
        'id': r.id,
        'user_id': r.user_id,
        'locker_id': r.locker_id,
        'start_time': r.start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': r.end_time.strftime('%Y-%m-%d %H:%M:%S'),
        'status': r.status
    } for r in reservations])

@app.route('/api/payments', methods=['GET'])
@login_required
def get_payments():
    payments = Payment.query.all()
    return jsonify([{
        'id': p.id,
        'user_id': p.user_id,
        'amount': float(p.amount),
        'status': p.status,
        'payment_date': p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else None
    } for p in payments])

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    notifications = [
        {
            'id': 1,
            'title': 'New Reservation',
            'message': 'Emma Wilson made a reservation for Locker #108',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'info'
        },
        {
            'id': 2,
            'title': 'Payment Pending',
            'message': 'Ahmet Yılmaz has a pending payment of $50.00',
            'timestamp': (datetime.utcnow() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'warning'
        },
        {
            'id': 3,
            'title': 'Locker Vacancy',
            'message': 'Locker #104 will be vacated by Zeynep Demir in 12 hours',
            'timestamp': (datetime.utcnow() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'warning'
        },
        {
            'id': 4,
            'title': 'Payment Received',
            'message': 'Payment of $45.00 received from Can ÖztÜrk',
            'timestamp': (datetime.utcnow() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'success'
        },
        {
            'id': 5,
            'title': 'Locker Maintenance',
            'message': 'Lockers #102, #105, #107, and #110 are ready for use',
            'timestamp': (datetime.utcnow() - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'info'
        },
        {
            'id': 6,
            'title': 'Long-term Reservation',
            'message': 'Mehmet Kaya rented Locker #106 for 2 days',
            'timestamp': (datetime.utcnow() - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'info'
        },
        {
            'id': 7,
            'title': 'New Customers',
            'message': 'Maria Garcia and Hans Schmidt have registered',
            'timestamp': (datetime.utcnow() - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'success'
        }
    ]
    return jsonify(notifications)

@app.route('/api/customers', methods=['GET'])
def get_customers():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    customers = User.query.filter_by(role='customer').all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None,
        'active': user.active
    } for user in customers])

@app.route('/api/customers', methods=['POST'])
def create_customer():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data or not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    customer = User(
        username=data['username'],
        email=data['email'],
        role='customer',
        active=True,
        created_at=datetime.utcnow()
    )
    customer.set_password(data['password'])
    
    try:
        db.session.add(customer)
        db.session.commit()
        return jsonify({
            'id': customer.id,
            'username': customer.username,
            'email': customer.email,
            'role': customer.role,
            'created_at': customer.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'active': customer.active
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create customer'}), 500

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    customer = User.query.filter_by(id=customer_id, role='customer').first()
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'username' in data:
        existing = User.query.filter_by(username=data['username']).first()
        if existing and existing.id != customer_id:
            return jsonify({'error': 'Username already exists'}), 400
        customer.username = data['username']
    
    if 'email' in data:
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != customer_id:
            return jsonify({'error': 'Email already exists'}), 400
        customer.email = data['email']
    
    if 'password' in data:
        customer.set_password(data['password'])
    
    if 'active' in data:
        customer.active = bool(data['active'])
    
    try:
        db.session.commit()
        return jsonify({
            'id': customer.id,
            'username': customer.username,
            'email': customer.email,
            'role': customer.role,
            'created_at': customer.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'active': customer.active
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update customer'}), 500

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    customer = User.query.filter_by(id=customer_id, role='customer').first()
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    
    try:
        # Instead of deleting, we can deactivate the customer
        customer.active = False
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete customer'}), 500

# Add sample data creation function
def create_sample_data():
    # Create sample users first
    if not User.query.filter_by(username='john_doe').first():
        users = [
            User(username='john_doe', email='john@example.com', role='customer'),
            User(username='maria_garcia', email='maria@example.com', role='customer'),
            User(username='ahmet_yilmaz', email='ahmet@example.com', role='customer'),
            User(username='zeynep_demir', email='zeynep@example.com', role='customer'),
            User(username='hans_schmidt', email='hans@example.com', role='customer'),
            User(username='mehmet_kaya', email='mehmet@example.com', role='customer'),
            User(username='ayse_celik', email='ayse@example.com', role='customer'),
            User(username='emma_wilson', email='emma@example.com', role='customer'),
            User(username='can_ozturk', email='can@example.com', role='customer'),
            User(username='sofia_rossi', email='sofia@example.com', role='customer'),
            User(username='murat_kaya', email='murat@example.com', role='customer'),
            User(username='seyda_demir', email='seyda@example.com', role='customer'),
            User(username='ali_yildiz', email='ali@example.com', role='customer'),
            User(username='fatma_sahin', email='fatma@example.com', role='customer'),
            User(username='deniz_arslan', email='deniz@example.com', role='customer')
        ]
        for user in users:
            user.set_password('password123')
            db.session.add(user)
        db.session.commit()

    # Create sample lockers with some empty ones
    if not Locker.query.first():
        lockers = [
            Locker(number='L101', status='occupied', assigned_user_id=11, assigned_user_name='Murat Kaya'),
            Locker(number='L102', status='occupied', assigned_user_id=12, assigned_user_name='Şeyda Demir'),
            Locker(number='L103', status='occupied', assigned_user_id=3, assigned_user_name='Ahmet Yılmaz'),
            Locker(number='L104', status='occupied', assigned_user_id=4, assigned_user_name='Zeynep Demir'),
            Locker(number='L105', status='available', assigned_user_id=None, assigned_user_name=None),
            Locker(number='L106', status='occupied', assigned_user_id=6, assigned_user_name='Mehmet Kaya'),
            Locker(number='L107', status='available', assigned_user_id=None, assigned_user_name=None),
            Locker(number='L108', status='occupied', assigned_user_id=8, assigned_user_name='Emma Wilson'),
            Locker(number='L109', status='occupied', assigned_user_id=9, assigned_user_name='Can Öztürk'),
            Locker(number='L110', status='available', assigned_user_id=None, assigned_user_name=None),
            Locker(number='L111', status='occupied', assigned_user_id=2, assigned_user_name='Maria Garcia'),
            Locker(number='L112', status='occupied', assigned_user_id=5, assigned_user_name='Hans Schmidt'),
            Locker(number='L113', status='available', assigned_user_id=None, assigned_user_name=None),
            Locker(number='L114', status='occupied', assigned_user_id=13, assigned_user_name='Ali Yıldız'),
            Locker(number='L115', status='occupied', assigned_user_id=14, assigned_user_name='Fatma Şahin')
        ]
        for locker in lockers:
            db.session.add(locker)
        db.session.commit()

    # Create sample reservations with mixed statuses
    if not Reservation.query.first():
        reservations = [
            Reservation(user_id=12, locker_id=2, start_time=datetime.utcnow(), 
                      end_time=datetime.utcnow() + timedelta(hours=2), status='active'),
            Reservation(user_id=3, locker_id=3, start_time=datetime.utcnow() - timedelta(hours=2),
                      end_time=datetime.utcnow() + timedelta(hours=22), status='active'),
            Reservation(user_id=4, locker_id=4, start_time=datetime.utcnow() - timedelta(days=1),
                      end_time=datetime.utcnow() + timedelta(hours=12), status='active'),
            Reservation(user_id=6, locker_id=6, start_time=datetime.utcnow(),
                      end_time=datetime.utcnow() + timedelta(days=2), status='active'),
            Reservation(user_id=8, locker_id=8, start_time=datetime.utcnow() + timedelta(days=1),
                      end_time=datetime.utcnow() + timedelta(days=3), status='pending'),
            Reservation(user_id=9, locker_id=9, start_time=datetime.utcnow(),
                      end_time=datetime.utcnow() + timedelta(hours=48), status='active'),
            Reservation(user_id=13, locker_id=14, start_time=datetime.utcnow(),
                      end_time=datetime.utcnow() + timedelta(hours=4), status='active'),
            Reservation(user_id=14, locker_id=15, start_time=datetime.utcnow(),
                      end_time=datetime.utcnow() + timedelta(hours=6), status='pending'),
            Reservation(user_id=11, locker_id=1, start_time=datetime.utcnow(),
                      end_time=datetime.utcnow() + timedelta(hours=1), status='active')
        ]
        for reservation in reservations:
            db.session.add(reservation)
        db.session.commit()

    # Create sample payments with different amounts and statuses
    if not Payment.query.first():
        payments = [
            Payment(user_id=1, amount=25.00, status='completed'),
            Payment(user_id=3, amount=50.00, status='pending'),
            Payment(user_id=4, amount=15.00, status='completed'),
            Payment(user_id=6, amount=75.00, status='completed'),
            Payment(user_id=8, amount=30.00, status='pending'),
            Payment(user_id=9, amount=45.00, status='completed'),
            Payment(user_id=11, amount=20.00, status='pending'),
            Payment(user_id=12, amount=35.00, status='completed'),
            Payment(user_id=13, amount=40.00, status='pending'),
            Payment(user_id=14, amount=55.00, status='completed'),
            Payment(user_id=15, amount=60.00, status='pending')
        ]
        for payment in payments:
            db.session.add(payment)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()  # Drop all tables
        db.create_all()  # Create all tables
        create_admin_user()  # Create admin user
        create_sample_data()  # Create sample data
    app.run(debug=True) 