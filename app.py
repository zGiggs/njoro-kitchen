from flask import Flask, render_template, session, redirect, url_for, request, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'njoro-kitchen-secret-key-2026'

# USE LOCAL DATABASE FILE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///njoro_kitchen.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ... rest of your code (keep everything else the same)
