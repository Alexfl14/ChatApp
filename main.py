import boto3
import uuid
import json
import os
from datetime import datetime
from decimal import Decimal
from flask import Flask, request, render_template, redirect, url_for, session
from flask_restful import Api, Resource
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
api = Api(app)

app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("No FLASK_SECRET_KEY set for Flask application")

aws_region = os.getenv('AWS_REGION')
users_table_name = os.getenv('DYNAMODB_USERS_TABLE')
messages_table_name = os.getenv('DYNAMODB_MESSAGES_TABLE')

dynamodb = boto3.resource('dynamodb', region_name=aws_region)
users_table = dynamodb.Table(users_table_name)
messages_table = dynamodb.Table(messages_table_name)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


def create_conversation_id(user1, user2):
    return '#'.join(sorted([user1, user2]))


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('welcome'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        if not username:
            return render_template("login.html", error="Username is required")

        try:
            response = users_table.get_item(Key={'username': username})
            if 'Item' not in response:
                users_table.put_item(Item={
                    'username': username,
                    'created_at': datetime.utcnow().isoformat(),
                    'last_active': datetime.utcnow().isoformat()
                })
            else:
                users_table.update_item(
                    Key={'username': username},
                    UpdateExpression='SET last_active = :la',
                    ExpressionAttributeValues={':la': datetime.utcnow().isoformat()}
                )
            session['username'] = username
            return redirect(url_for('welcome'))
        except Exception as e:
            return render_template("login.html", error=f"Error: {str(e)}")

    return render_template("login.html")


@app.route('/welcome')
def welcome():
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        response = users_table.scan()
        users = response.get('Items', [])
        users.sort(key=lambda x: x['username'])
        return render_template("welcome.html",
                               users=users,
                               current_user=session['username'])
    except Exception as e:
        return f"Error loading users: {str(e)}"


@app.route('/chat/<other_user>', methods=['GET', 'POST'])
def chat(other_user):
    if 'username' not in session:
        return redirect(url_for('login'))
    current_user = session['username']
    if current_user == other_user:
        return redirect(url_for('welcome'))

    conversation_id = create_conversation_id(current_user, other_user)
    if request.method == 'POST':
        message_text = request.form['message'].strip()
        if message_text:
            try:
                messages_table.put_item(Item={
                    'message_jd': str(uuid.uuid4()),
                    'conversation_id': conversation_id,
                    'timestamp': int(datetime.utcnow().timestamp() * 1000),
                    'from_user': current_user,
                    'to_user': other_user,
                    'message_text': message_text,
                    'created_at': datetime.utcnow().isoformat()
                })
                return redirect(url_for('chat', other_user=other_user))
            except Exception as e:
                return f"Error sending message: {str(e)}"
    try:
        response = messages_table.query(
            IndexName='UserConversation',
            KeyConditionExpression='conversation_id = :cid',
            ExpressionAttributeValues={':cid': conversation_id},
            ScanIndexForward=False,
            Limit=25
        )
        messages = response.get('Items', [])
        messages.reverse()
        return render_template("chat.html",
                               messages=messages,
                               current_user=current_user,
                               other_user=other_user)
    except Exception as e:
        return f"Error loading chat: {str(e)}"


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/health')
def health():
    try:
        users_table.table_status
        messages_table.table_status
        return {'status': 'OK', 'timestamp': datetime.utcnow().isoformat()}, 200
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e)}, 500


class UserList(Resource):
    def get(self):
        try:
            response = users_table.scan()
            return {'users': response.get('Items', [])}, 200
        except Exception as e:
            return {'error': str(e)}, 500


class Messages(Resource):
    def get(self, user1, user2):
        try:
            conversation_id = create_conversation_id(user1, user2)
            response = messages_table.query(
                IndexName='UserConversation',
                KeyConditionExpression='conversation_id = :cid',
                ExpressionAttributeValues={':cid': conversation_id},
                ScanIndexForward=False,
                Limit=50
            )
            return {'messages': response.get('Items', [])}, 200
        except Exception as e:
            return {'error': str(e)}, 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)