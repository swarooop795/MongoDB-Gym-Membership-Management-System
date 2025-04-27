import os
from datetime import datetime, timedelta
from functools import wraps
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
    Flask, render_template, request, redirect, 
    url_for, flash, session, abort, make_response
)
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Better to use a fixed secret key in production

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['GymDB']
members_collection = db['members']
subscriptions_collection = db['subscriptions']
admin_collection = db['admin']

# Create templates directory if it doesn't exist
os.makedirs('templates', exist_ok=True)

def initialize_sample_data():
    # Create indexes for better performance
    members_collection.create_index([("subscription.expiry_date", ASCENDING)])
    members_collection.create_index([("subscription.plan_id", ASCENDING)])
    members_collection.create_index([("name", ASCENDING)])
    admin_collection.create_index([("username", ASCENDING)], unique=True)
    
    if subscriptions_collection.count_documents({}) == 0:
        subscriptions_collection.insert_many([
            {"plan_id": 1, "plan_name": "Basic", "price": 50, "duration": "1 Month", "duration_days": 30},
            {"plan_id": 2, "plan_name": "Standard", "price": 120, "duration": "3 Months", "duration_days": 90},
            {"plan_id": 3, "plan_name": "Premium", "price": 400, "duration": "1 Year", "duration_days": 365}
        ])

    if members_collection.count_documents({}) == 0:
        members_collection.insert_many([
            {
                "name": "John Doe",
                "age": 28,
                "gender": "male",
                "contact": "123-456-7890",
                "email": "john@example.com",
                "address": "123 Main St",
                "emergency_contact": "Jane Doe (987-654-3210)",
                "health_notes": "Allergic to peanuts",
                "subscription": {
                    "plan_id": 2,
                    "start_date": datetime(2024, 3, 1),
                    "expiry_date": datetime(2024, 6, 1),
                    "status": "active",
                    "payments": [
                        { "date": datetime(2024, 3, 1), "method": "credit card"}
                    ]
                },
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "name": "Jane Smith",
                "age": 30,
                "gender": "female",
                "contact": "987-654-3210",
                "email": "jane@example.com",
                "address": "456 Oak Ave",
                "emergency_contact": "John Smith (123-456-7890)",
                "health_notes": "None",
                "subscription": {
                    "plan_id": 3,
                    "start_date": datetime(2024, 1, 10),
                    "expiry_date": datetime(2025, 1, 10),
                    "status": "active",
                    "payments": [
                        {"date": datetime(2024, 1, 10), "method": "bank transfer"}
                    ]
                },
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ])
    
    if admin_collection.count_documents({}) == 0:
        admin_collection.insert_one({
            "username": "admin",
            "password": generate_password_hash("admin123"),
            "full_name": "Administrator",
            "created_at": datetime.now(),
            "last_login": None
        })

def create_templates():
    login_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login Gym Management System</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary: #4361ee;
            --secondary: #3f37c9;
            --accent: #4895ef;
            --danger: #f72585;
            --success: #4cc9f0;
            --light: #f8f9fa;
            --dark: #212529;
            --gray: #6c757d;
            --light-gray: #e9ecef;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.7)), 
                        url('https://vigyr.com/wp-content/uploads/2020/01/features-of-best-gym-management-systems-scaled.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: var(--dark);
            line-height: 1.6;
        }
        
        .login-container {
            width: 100%;
            max-width: 400px;
            padding: 2rem;
        }
        
        .login-card {
            background: rgba(255, 255, 255, 0.81);
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .login-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 5px;
            height: 100%;
            background: linear-gradient(to bottom, var(--primary), var(--accent));
        }
        
        .login-card h1 {
            color: var(--primary);
            margin-bottom: 1.5rem;
            font-size: 1.8rem;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
            text-align: left;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--dark);
        }
        
        input {
            width: 100%;
            padding: 0.8rem;
            border: 1px solid var(--light-gray);
            border-radius: 6px;
            font-size: 1rem;
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }
        
        input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(72, 149, 239, 0.2);
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: linear-gradient(to right, var(--primary), var(--secondary));
            color: white;
            padding: 0.8rem 1.5rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(67, 97, 238, 0.3);
            width: 100%;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 7px 15px rgba(67, 97, 238, 0.4);
        }
        
        .alert {
            padding: 1rem;
            margin-bottom: 1.5rem;
            border-radius: 6px;
            font-weight: 500;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            animation: slideIn 0.5s ease-out;
        }
        
        .alert-danger {
            background-color: rgba(247, 37, 133, 0.1);
            border-left: 4px solid var(--danger);
            color: var(--danger);
        }
        
        @keyframes slideIn {
            from {
                transform: translateY(-20px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        .input-icon {
            position: relative;
        }
        
        .input-icon i {
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--gray);
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-card">
            <h1>
                <i class="fas fa-lock"></i>Gym Membership Admin Login
            </h1>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">
                            <i class="fas fa-{% if category == 'success' %}check-circle{% else %}exclamation-circle{% endif %}"></i>
                            {{ message }}
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form action="/login" method="POST">
                <div class="form-group">
                    <label for="username"><i class="fas fa-user"></i> Username:</label>
                    <div class="input-icon">
                        <input type="text" id="username" name="username" required placeholder="Enter admin username">
                        <i class="fas fa-user-shield"></i>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="password"><i class="fas fa-key"></i> Password:</label>
                    <div class="input-icon">
                        <input type="password" id="password" name="password" required placeholder="Enter password">
                        <i class="fas fa-lock"></i>
                    </div>
                </div>
                
                <button type="submit" class="btn">
                    <i class="fas fa-sign-in-alt"></i> Login
                </button>
            </form>
        </div>
    </div>
</body>
</html>"""

    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gym Membership Management</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary: #4361ee;
            --secondary: #3f37c9;
            --accent: #4895ef;
            --danger: #f72585;
            --success: #4cc9f0;
            --light: #f8f9fa;
            --dark: #212529;
            --gray: #6c757d;
            --light-gray: #e9ecef;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                        url('https://vigyr.com/wp-content/uploads/2020/01/features-of-best-gym-management-systems-scaled.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            min-height: 100vh;
            color: var(--light);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(to right, rgba(67, 97, 238, 0.9), rgba(63, 55, 201, 0.9));
            color: white;
            padding: 1.5rem 0;
            margin-bottom: 2rem;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        header::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 65%, rgba(255,255,255,0.2) 100%);
            pointer-events: none;
        }
        
        header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            position: relative;
            z-index: 1;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
        }
        
        .logout-btn {
            position: absolute;
            right: 20px;
            top: 20px;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .logout-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .card {
            background: rgba(255, 255, 255, 0.77);;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4);
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 5px;
            height: 100%;
            background: linear-gradient(to bottom, var(--primary), var(--accent));
        }
        
        .card h2 {
            color: var(--primary);
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card h2 i {
            color: var(--accent);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        
        table th {
            background: linear-gradient(to right, var(--primary), var(--secondary));
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-weight: 500;
        }
        
        table td {
            padding: 12px 15px;
            border-bottom: 1px solid var(--light-gray);
            vertical-align: middle;
            color: var(--dark);
        }
        
        table tr:nth-child(even) {
            background-color: rgba(67, 97, 238, 0.1);
        }
        
        table tr:hover {
            background-color: rgba(67, 97, 238, 0.2);
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: linear-gradient(to right, var(--primary), var(--secondary));
            color: white;
            padding: 0.6rem 1.2rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(67, 97, 238, 0.4);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(67, 97, 238, 0.6);
            color: white;
        }
        
        .btn-danger {
            background: linear-gradient(to right, var(--danger), #d81159);
        }
        
        .btn-danger:hover {
            box-shadow: 0 5px 15px rgba(247, 37, 133, 0.6);
        }
        
        .btn-secondary {
            background: linear-gradient(to right, var(--gray), #5a6268);
        }
        
        .btn-secondary:hover {
            box-shadow: 0 5px 15px rgba(108, 117, 125, 0.6);
        }
        
        .btn-info {
            background: linear-gradient(to right, #17a2b8, #138496);
        }
        
        .btn-info:hover {
            box-shadow: 0 5px 15px rgba(23, 162, 184, 0.6);
        }
        
        .form-group {
            margin-bottom: 1.2rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--dark);
        }
        
        input, select {
            width: 100%;
            padding: 0.8rem;
            border: 1px solid var(--light-gray);
            border-radius: 6px;
            font-size: 1rem;
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(72, 149, 239, 0.3);
        }
        
        .status-active {
            color: #2ecc71;
            font-weight: 600;
        }
        
        .status-expired {
            color: var(--danger);
            font-weight: 600;
        }
        
        .alert {
            padding: 1rem;
            margin-bottom: 1.5rem;
            border-radius: 6px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.5s ease-out;
        }
        
        .alert-success {
            background-color: rgba(76, 201, 240, 0.3);
            border-left: 4px solid var(--success);
            color: white;
        }
        
        .badge {
            display: inline-block;
            padding: 0.35em 0.65em;
            font-size: 0.75em;
            font-weight: 700;
            line-height: 1;
            color: #fff;
            text-align: center;
            white-space: nowrap;
            vertical-align: baseline;
            border-radius: 50rem;
        }
        
        .badge-primary {
            background-color: var(--primary);
        }
        
        .badge-danger {
            background-color: var(--danger);
        }
        
        .badge-success {
            background-color: var(--success);
        }
        
        .action-buttons {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .plan-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 1rem;
        }
        
        .member-id {
            font-family: monospace;
            background-color: var(--light-gray);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.9rem;
        }
        
        @keyframes slideIn {
            from {
                transform: translateY(-20px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        @media (max-width: 768px) {
            table {
                display: block;
                overflow-x: auto;
                white-space: nowrap;
            }
            
            .container {
                padding: 15px;
            }
            
            header h1 {
                font-size: 2rem;
            }
            
            .card {
                padding: 1rem;
            }
            
            .logout-btn {
                position: static;
                margin-top: 10px;
            }
        }
        
        /* Floating animation for header */
        @keyframes floating {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }
        
        .floating {
            animation: floating 3s ease-in-out infinite;
        }
        
        /* Pulse animation for buttons */
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .pulse:hover {
            animation: pulse 1.5s infinite;
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1 class="floating">
                <i class="fas fa-dumbbell"></i> Gym Membership Management System
            </h1>
            <form action="/logout" method="POST">
                <button type="submit" class="logout-btn">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </button>
            </form>
        </div>
    </header>

    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">
                        <i class="fas fa-{% if category == 'success' %}check-circle{% else %}exclamation-circle{% endif %}"></i>
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <!-- Add Member Form -->
        <div class="card">
            <h2><i class="fas fa-user-plus"></i> Add New Member</h2>
            <form action="/add_member" method="POST">
                <div class="form-group">
                    <label for="name"><i class="fas fa-user"></i> Name:</label>
                    <input type="text" id="name" name="name" required placeholder="Enter member's full name">
                </div>
                <div class="form-group">
                    <label for="age"><i class="fas fa-birthday-cake"></i> Age:</label>
                    <input type="number" id="age" name="age" required placeholder="Enter member's age">
                </div>
                <div class="form-group">
                    <label for="contact"><i class="fas fa-phone"></i> Contact:</label>
                    <input type="text" id="contact" name="contact" required placeholder="Enter contact number">
                </div>
                <div class="form-group">
                    <label for="plan"><i class="fas fa-tag"></i> Membership Plan:</label>
                    <select id="plan" name="plan" required>
                        {% for plan in plans %}
                            <option value="{{ plan.plan_id }}">{{ plan.plan_name }} -Rs.{{plan.price }} ({{ plan.duration }})</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label for="method of payment"><i class="fas fa-bank"></i> Method of Payment:</label>
                    <input type="text" id="method of payment" name="method of payment" required placeholder="Enter payment method">
                </div>
                <div class="form-group">
                    <label for="start_date"><i class="fas fa-calendar-alt"></i> Start Date:</label>
                    <input type="date" id="start_date" name="start_date" required>
                </div>
                <div class="form-group">
                    <label for="expiry_date"><i class="fas fa-calendar-times"></i> Expiry Date:</label>
                    <input type="date" id="expiry_date" name="expiry_date" required>
                </div>
                <button type="submit" class="btn pulse">
                    <i class="fas fa-save"></i> Add Member
                </button>
            </form>
        </div>

        <!-- Members List -->
        <div class="card">
            <h2><i class="fas fa-users"></i> All Members</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Age</th>
                        <th>Contact</th>
                        <th>Plan</th>
                        <th>Start Date</th>
                        <th>Expiry Date</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for member in members %}
                        <tr>
                            <td><span class="member-id">{{ member._id }}</span></td>
                            <td>{{ member.name }}</td>
                            <td>{{ member.age }}</td>
                            <td>{{ member.contact }}</td>
                            <td>
                                {% for plan in plans %}
                                    {% if plan.plan_id == member.subscription.plan_id %}
                                        <span class="badge 
                                            {% if plan.plan_name == 'Premium' %}badge-primary
                                            {% elif plan.plan_name == 'Standard' %}badge-success
                                            {% else %}badge-secondary{% endif %}">
                                            {{ plan.plan_name }}
                                        </span>
                                    {% endif %}
                                {% endfor %}
                            </td>
                            <td>{{ member.subscription.start_date.strftime('%Y-%m-%d') }}</td>
                            <td>{{ member.subscription.expiry_date.strftime('%Y-%m-%d') }}</td>
                            <td class="{% if member.subscription.expiry_date > current_date %}status-active{% else %}status-expired{% endif %}">
                                {% if member.subscription.expiry_date > current_date %}
                                    <i class="fas fa-check-circle"></i> Active
                                {% else %}
                                    <i class="fas fa-times-circle"></i> Expired
                                {% endif %}
                            </td>
                            <td>
                                <div class="action-buttons">
                                    <a href="/view_member/{{ member._id }}" class="btn btn-info pulse">
                                        <i class="fas fa-eye"></i> View
                                    </a>
                                    <form action="/update_subscription/{{ member._id }}" method="POST" style="width: 100%; margin-top: 5px;">
                                        <select name="new_plan" required style="margin-bottom: 5px;">
                                            {% for plan in plans %}
                                                <option value="{{ plan.plan_id }}" {% if plan.plan_id == member.subscription.plan_id %}selected{% endif %}>
                                                    {{ plan.plan_name }}
                                                </option>
                                            {% endfor %}
                                        </select>
                                        <input type="date" name="start_date" value="{{ member.subscription.start_date.strftime('%Y-%m-%d') }}" required style="margin-bottom: 5px;">
                                        <input type="date" name="expiry_date" value="{{ member.subscription.expiry_date.strftime('%Y-%m-%d') }}" required style="margin-bottom: 5px;">
                                        <button type="submit" class="btn btn-secondary pulse" style="width: 100%;">
                                            <i class="fas fa-sync-alt"></i> Update
                                        </button>
                                    </form>
                                    <a href="/delete_member/{{ member._id }}" class="btn btn-danger pulse" style="width: 100%; margin-top: 5px;">
                                        <i class="fas fa-trash-alt"></i> Delete
                                    </a>
                                </div>
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Expired Members -->
        <div class="card">
            <h2><i class="fas fa-exclamation-triangle"></i> Expired Memberships</h2>
            {% if expired_members %}
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Plan</th>
                            <th>Expiry Date</th>
                            <th>Days Expired</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for member in expired_members %}
                            <tr>
                                <td><span class="member-id">{{ member._id }}</span></td>
                                <td>{{ member.name }}</td>
                                <td>
                                    {% for plan in plans %}
                                        {% if plan.plan_id == member.subscription.plan_id %}
                                            {{ plan.plan_name }}
                                        {% endif %}
                                    {% endfor %}
                                </td>
                                <td>{{ member.subscription.expiry_date.strftime('%Y-%m-%d') }}</td>
                                <td>
                                    <span class="badge badge-danger">
                                        {{ (current_date - member.subscription.expiry_date).days }} days
                                    </span>
                                </td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
                <a href="/delete_expired" class="btn btn-danger pulse" style="margin-top: 15px;">
                    <i class="fas fa-trash-alt"></i> Delete All Expired
                </a>
            {% else %}
                <p style="padding: 15px; background-color: var(--light-gray); border-radius: 6px;">
                    <i class="fas fa-check"></i> No expired memberships found.
                </p>
            {% endif %}
        </div>

        <!-- View by Plan -->
        <div class="card">
            <h2><i class="fas fa-filter"></i> View Members by Plan</h2>
            <div class="plan-buttons">
                {% for plan in plans %}
                    <a href="/members_by_plan/{{ plan.plan_id }}" class="btn pulse">
                        <i class="fas fa-{% if plan.plan_name == 'Premium' %}crown{% elif plan.plan_name == 'Standard' %}star{% else %}tag{% endif %}"></i> 
                        {{ plan.plan_name }}
                    </a>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>"""

    members_by_plan_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Members by Plan</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary: #4361ee;
            --secondary: #3f37c9;
            --accent: #4895ef;
            --danger: #f72585;
            --success: #4cc9f0;
            --light: #f8f9fa;
            --dark: #212529;
            --gray: #6c757d;
            --light-gray: #e9ecef;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                        url('https://vigyr.com/wp-content/uploads/2020/01/features-of-best-gym-management-systems-scaled.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            min-height: 100vh;
            color: var(--light);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(to right, rgba(67, 97, 238, 0.9), rgba(63, 55, 201, 0.9));
            color: white;
            padding: 1.5rem 0;
            margin-bottom: 2rem;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            position: relative;
            z-index: 1;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
        }
        
        .logout-btn {
            position: absolute;
            right: 20px;
            top: 20px;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .logout-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            padding: 1.5rem;
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card h2 {
            color: var(--primary);
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        
        table th {
            background: linear-gradient(to right, var(--primary), var(--secondary));
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-weight: 500;
        }
        
        table td {
            padding: 12px 15px;
            border-bottom: 1px solid var(--light-gray);
            color: var(--dark);
        }
        
        table tr:nth-child(even) {
            background-color: rgba(67, 97, 238, 0.1);
        }
        
        table tr:hover {
            background-color: rgba(67, 97, 238, 0.2);
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: linear-gradient(to right, var(--primary), var(--secondary));
            color: white;
            padding: 0.6rem 1.2rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(67, 97, 238, 0.4);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(67, 97, 238, 0.6);
            color: white;
        }
        
        .status-active {
            color: #2ecc71;
            font-weight: 600;
        }
        
        .status-expired {
            color: var(--danger);
            font-weight: 600;
        }
        
        .member-id {
            font-family: monospace;
            background-color: var(--light-gray);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            table {
                display: block;
                overflow-x: auto;
                white-space: nowrap;
            }
            
            .container {
                padding: 15px;
            }
            
            header h1 {
                font-size: 2rem;
            }
            
            .card {
                padding: 1rem;
            }
            
            .logout-btn {
                position: static;
                margin-top: 10px;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>
                <i class="fas fa-users"></i> Members with {{ plan.plan_name }} Plan
            </h1>
            <form action="/logout" method="POST">
                <button type="submit" class="logout-btn">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </button>
            </form>
        </div>
    </header>

    <div class="container">
        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Age</th>
                        <th>Contact</th>
                        <th>Start Date</th>
                        <th>Expiry Date</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for member in members %}
                        <tr>
                            <td><span class="member-id">{{ member._id }}</span></td>
                            <td>{{ member.name }}</td>
                            <td>{{ member.age }}</td>
                            <td>{{ member.contact }}</td>
                            <td>{{ member.subscription.start_date.strftime('%Y-%m-%d') }}</td>
                            <td>{{ member.subscription.expiry_date.strftime('%Y-%m-%d') }}</td>
                            <td class="{% if member.subscription.expiry_date > current_date %}status-active{% else %}status-expired{% endif %}">
                                {% if member.subscription.expiry_date > current_date %}
                                    <i class="fas fa-check-circle"></i> Active
                                {% else %}
                                    <i class="fas fa-times-circle"></i> Expired
                                {% endif %}
                            </td>
                            <td>
                                <a href="/view_member/{{ member._id }}" class="btn btn-info">
                                    <i class="fas fa-eye"></i> View
                                </a>
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
            <a href="/" class="btn" style="margin-top: 20px;">
                <i class="fas fa-arrow-left"></i> Back to Dashboard
            </a>
        </div>
    </div>
</body>
</html>"""

    view_member_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Member Details</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary: #4361ee;
            --secondary: #3f37c9;
            --accent: #4895ef;
            --danger: #f72585;
            --success: #4cc9f0;
            --light: #f8f9fa;
            --dark: #212529;
            --gray: #6c757d;
            --light-gray: #e9ecef;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                        url('https://vigyr.com/wp-content/uploads/2020/01/features-of-best-gym-management-systems-scaled.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            min-height: 100vh;
            color: var(--light);
            line-height: 1.6;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(to right, rgba(67, 97, 238, 0.9), rgba(63, 55, 201, 0.9));
            color: white;
            padding: 1.5rem 0;
            margin-bottom: 2rem;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            position: relative;
            z-index: 1;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
        }
        
        .logout-btn {
            position: absolute;
            right: 20px;
            top: 20px;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .logout-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 5px;
            height: 100%;
            background: linear-gradient(to bottom, var(--primary), var(--accent));
        }
        
        .card h2 {
            color: var(--primary);
            margin-bottom: 1.5rem;
            font-size: 1.8rem;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 2px solid var(--light-gray);
            padding-bottom: 10px;
        }
        
        .member-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .info-group {
            margin-bottom: 1rem;
        }
        
        .info-label {
            font-weight: 600;
            color: var(--dark);
            margin-bottom: 0.3rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .info-value {
            padding: 0.8rem;
            background-color: var(--light-gray);
            border-radius: 6px;
            color: var(--dark);
        }
        
        .status-active {
            color: #2ecc71;
            font-weight: 600;
        }
        
        .status-expired {
            color: var(--danger);
            font-weight: 600;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: linear-gradient(to right, var(--primary), var(--secondary));
            color: white;
            padding: 0.8rem 1.5rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(67, 97, 238, 0.3);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 7px 15px rgba(67, 97, 238, 0.4);
            color: white;
        }
        
        .btn-print {
            background: linear-gradient(to right, #6c757d, #5a6268);
            margin-right: 10px;
        }
        
        .btn-back {
            background: linear-gradient(to right, #17a2b8, #138496);
        }
        
        .print-only {
            display: none;
        }
        
        @media print {
            body {
                background: none;
                color: var(--dark);
            }
            
            header, .btn-container {
                display: none;
            }
            
            .card {
                box-shadow: none;
                background: none;
                padding: 0;
            }
            
            .print-only {
                display: block;
                text-align: center;
                margin-bottom: 2rem;
            }
            
            .print-only h2 {
                color: var(--primary);
                border-bottom: 2px solid var(--primary);
                padding-bottom: 10px;
            }
            
            .card::before {
                display: none;
            }
        }
        
        @media (max-width: 768px) {
            .member-info {
                grid-template-columns: 1fr;
            }
            
            .container {
                padding: 15px;
            }
            
            header h1 {
                font-size: 1.8rem;
            }
            
            .logout-btn {
                position: static;
                margin-top: 10px;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>
                <i class="fas fa-user"></i> Member Details
            </h1>
            <form action="/logout" method="POST">
                <button type="submit" class="logout-btn">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </button>
            </form>
        </div>
    </header>

    <div class="container">
        <div class="card">
            <div class="print-only">
                <h2><i class="fas fa-dumbbell"></i> Gym Membership Card</h2>
                <p>Printed on: {{ current_date.strftime('%Y-%m-%d %H:%M:%S') }}</p>
            </div>
            
            <h2>
                <i class="fas fa-user-circle"></i> {{ member.name }}
                <span class="{% if member.subscription.expiry_date > current_date %}status-active{% else %}status-expired{% endif %}" style="font-size: 1rem; margin-left: 15px;">
                    {% if member.subscription.expiry_date > current_date %}
                        <i class="fas fa-check-circle"></i> Active
                    {% else %}
                        <i class="fas fa-times-circle"></i> Expired
                    {% endif %}
                </span>
            </h2>
            
            <div class="member-info">
                <div>
                    <div class="info-group">
                        <div class="info-label">
                            <i class="fas fa-id-card"></i> Member ID:
                        </div>
                        <div class="info-value">
                            {{ member._id }}
                        </div>
                    </div>
                    
                    <div class="info-group">
                        <div class="info-label">
                            <i class="fas fa-birthday-cake"></i> Age:
                        </div>
                        <div class="info-value">
                            {{ member.age }}
                        </div>
                    </div>
                    
                    <div class="info-group">
                        <div class="info-label">
                            <i class="fas fa-phone"></i> Contact:
                        </div>
                        <div class="info-value">
                            {{ member.contact }}
                        </div>
                    </div>
                    
                    <div class="info-group">
                        <div class="info-label">
                            <i class="fas fa-envelope"></i> Email:
                        </div>
                        <div class="info-value">
                            {{ member.email or 'N/A' }}
                        </div>
                    </div>
                </div>
                
                <div>
                    <div class="info-group">
                        <div class="info-label">
                            <i class="fas fa-home"></i> Address:
                        </div>
                        <div class="info-value">
                            {{ member.address or 'N/A' }}
                        </div>
                    </div>
                    
                    <div class="info-group">
                        <div class="info-label">
                            <i class="fas fa-user-md"></i> Emergency Contact:
                        </div>
                        <div class="info-value">
                            {{ member.emergency_contact or 'N/A' }}
                        </div>
                    </div>
                    
                    <div class="info-group">
                        <div class="info-label">
                            <i class="fas fa-heartbeat"></i> Health Notes:
                        </div>
                        <div class="info-value">
                            {{ member.health_notes or 'None' }}
                        </div>
                    </div>
                </div>
            </div>
            
            <h2><i class="fas fa-id-badge"></i> Membership Details</h2>
            
            <div class="member-info">
                <div>
                    <div class="info-group">
                        <div class="info-label">
                            <i class="fas fa-tag"></i> Plan:
                        </div>
                        <div class="info-value">
                            {% for plan in plans %}
                                {% if plan.plan_id == member.subscription.plan_id %}
                                    {{ plan.plan_name }} ({{ plan.duration }} - Rs.{{ plan.price }})
                                {% endif %}
                            {% endfor %}
                        </div>
                    </div>
                    
                    <div class="info-group">
                        <div class="info-label">
                            <i class="fas fa-calendar-check"></i> Start Date:
                        </div>
                        <div class="info-value">
                            {{ member.subscription.start_date.strftime('%Y-%m-%d') }}
                        </div>
                    </div>
                </div>
                
                <div>
                    <div class="info-group">
                        <div class="info-label">
                            <i class="fas fa-calendar-times"></i> Expiry Date:
                        </div>
                        <div class="info-value">
                            {{ member.subscription.expiry_date.strftime('%Y-%m-%d') }}
                            ({{ (member.subscription.expiry_date - current_date).days }} days remaining)
                        </div>
                    </div>
                    
                    <div class="info-group">
                        <div class="info-label">
                            <i class="fas fa-clock"></i> Member Since:
                        </div>
                        <div class="info-value">
                            {{ member.created_at.strftime('%Y-%m-%d') }}
                            ({{ (current_date - member.created_at).days }} days)
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="btn-container" style="margin-top: 2rem; text-align: center;">
                <button onclick="window.print()" class="btn btn-print">
                    <i class="fas fa-print"></i> Print Membership
                </button>
                <a href="/" class="btn btn-back">
                    <i class="fas fa-arrow-left"></i> Back to Dashboard
                </a>
            </div>
        </div>
    </div>
</body>
</html>"""

    with open('templates/login.html', 'w') as f:
        f.write(login_html)

    with open('templates/index.html', 'w') as f:
        f.write(index_html)

    with open('templates/members_by_plan.html', 'w') as f:
        f.write(members_by_plan_html)

    with open('templates/view_member.html', 'w') as f:
        f.write(view_member_html)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access this page', 'danger')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = admin_collection.find_one({"username": username})
        if admin and check_password_hash(admin['password'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_full_name'] = admin.get('full_name', 'Admin')
            
            # Update last login
            admin_collection.update_one(
                {"username": username},
                {"$set": {"last_login": datetime.now()}}
            )
            
            flash('Login successful!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/')
@login_required
def dashboard():
    try:
        members = list(members_collection.find().sort("name", ASCENDING))
        plans = list(subscriptions_collection.find())
        expired_members = list(members_collection.find(
            {"subscription.expiry_date": {"$lt": datetime.now()}}
        ).sort("subscription.expiry_date", ASCENDING))
        
        return render_template('index.html', 
                            members=members, 
                            plans=plans, 
                            expired_members=expired_members,
                            current_date=datetime.now())
    except Exception as e:
        flash(f"Error loading data: {str(e)}", "danger")
        return render_template('index.html', 
                            members=[], 
                            plans=[], 
                            expired_members=[],
                            current_date=datetime.now())

@app.route('/add_member', methods=['POST'])
@login_required
def add_member():
    try:
        name = request.form.get('name')
        age = int(request.form.get('age'))
        contact = request.form.get('contact')
        plan_id = int(request.form.get('plan'))
        method_payment=request.form.get('method of payment')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        expiry_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d')
        
        # Validate dates
        if expiry_date <= start_date:
            flash("Expiry date must be after start date", "danger")
            return redirect(url_for('dashboard'))
        
        member_data = {
            "name": name,
            "age": age,
            "contact": contact,
            "subscription": {
                "plan_id": plan_id,
                "method_payment":method_payment,
                "start_date": start_date,
                "expiry_date": expiry_date,
                "status": "active"
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        result = members_collection.insert_one(member_data)
        flash(f"Member added successfully! Member ID: {result.inserted_id}", "success")
    except ValueError as ve:
        flash(f"Invalid input: {str(ve)}", "danger")
    except Exception as e:
        flash(f"Error adding member: {str(e)}", "danger")
    
    return redirect(url_for('dashboard'))

@app.route('/update_subscription/<member_id>', methods=['POST'])
@login_required
def update_subscription(member_id):
    try:
        new_plan_id = int(request.form.get('new_plan'))
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        expiry_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d')
        
        # Validate dates
        if expiry_date <= start_date:
            flash("Expiry date must be after start date", "danger")
            return redirect(url_for('dashboard'))
        
        result = members_collection.update_one(
            {"_id": ObjectId(member_id)},
            {"$set": {
                "subscription.plan_id": new_plan_id,
                "subscription.start_date": start_date,
                "subscription.expiry_date": expiry_date,
                "updated_at": datetime.now()
            }}
        )
        
        if result.modified_count > 0:
            flash("Subscription updated successfully!", "success")
        else:
            flash("No changes made or member not found", "warning")
    except Exception as e:
        flash(f"Error updating subscription: {str(e)}", "danger")
    
    return redirect(url_for('dashboard'))

@app.route('/delete_member/<member_id>')
@login_required
def delete_member(member_id):
    try:
        result = members_collection.delete_one({"_id": ObjectId(member_id)})
        if result.deleted_count > 0:
            flash("Member deleted successfully!", "success")
        else:
            flash("Member not found", "warning")
    except Exception as e:
        flash(f"Error deleting member: {str(e)}", "danger")
    
    return redirect(url_for('dashboard'))

@app.route('/delete_expired')
@login_required
def delete_expired():
    try:
        result = members_collection.delete_many({"subscription.expiry_date": {"$lt": datetime.now()}})
        flash(f"Deleted {result.deleted_count} expired memberships", "success")
    except Exception as e:
        flash(f"Error deleting expired members: {str(e)}", "danger")
    
    return redirect(url_for('dashboard'))

@app.route('/members_by_plan/<plan_id>')
@login_required
def members_by_plan(plan_id):
    try:
        members = list(members_collection.find(
            {"subscription.plan_id": int(plan_id)}
        ).sort("name", ASCENDING))
        
        plan = subscriptions_collection.find_one({"plan_id": int(plan_id)})
        
        if not plan:
            flash("Plan not found", "danger")
            return redirect(url_for('dashboard'))
            
        return render_template('members_by_plan.html', 
                            members=members, 
                            plan=plan,
                            current_date=datetime.now())
    except Exception as e:
        flash(f"Error loading members: {str(e)}", "danger")
        return redirect(url_for('dashboard'))
    
@app.route('/view_member/<member_id>')
@login_required
def view_member(member_id):
    try:
        member = members_collection.find_one({"_id": ObjectId(member_id)})
        if not member:
            flash("Member not found", "danger")
            return redirect(url_for('dashboard'))
        
        plans = list(subscriptions_collection.find())
        
        return render_template('view_member.html',
                            member=member,
                            plans=plans,
                            current_date=datetime.now())
    except Exception as e:
        flash(f"Error loading member details: {str(e)}", "danger")
        return redirect(url_for('dashboard'))

@app.route('/print_member/<member_id>')
@login_required
def print_member(member_id):
    try:
        member = members_collection.find_one({"_id": ObjectId(member_id)})
        if not member:
            flash("Member not found", "danger")
            return redirect(url_for('dashboard'))
        
        plans = list(subscriptions_collection.find())
        
        # Generate PDF or print-friendly HTML
        rendered = render_template('view_member.html',
                                 member=member,
                                 plans=plans,
                                 current_date=datetime.now())
        
        response = make_response(rendered)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=member_{member_id}.pdf'
        return response
    except Exception as e:
        flash(f"Error generating print view: {str(e)}", "danger")
        return redirect(url_for('dashboard'))

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

# Initialize data and templates
initialize_sample_data()
create_templates()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)