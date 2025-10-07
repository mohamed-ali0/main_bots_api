#!/usr/bin/env python
'''
Helper script to set session ID for user
'''

from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    user = User.query.get(1)
    if user:
        user.session_id = 'session_1759763507_-8222151154545660229'
        db.session.commit()
        print(f'Session ID set for user {user.username}')
        print(f'   Session ID: {user.session_id}')
    else:
        print('User not found')
