from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from decouple import config
import yaml
import random
import re
import json
import spacy


app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = config('FLASK_SECRET_KEY')

def load_users_from_file():
    try:
        with open('users.json', 'r') as file:
            users = json.load(file)
    except FileNotFoundError:
        users = {}
    return users

def save_users_to_file(users):
    with open('users.json', 'w') as file:
        json.dump(users, file)

def load_signup_data_from_file():
    try:
        with open('signup_data.txt', 'r') as file:
            content = file.read()
            if content:
                signup_data = json.loads(content)
            else:
                signup_data = []
    except FileNotFoundError:
        signup_data = []
    except json.JSONDecodeError:
        signup_data = []
    return signup_data


def save_signup_data_to_file(signup_data):
    with open('signup_data.txt', 'w') as file:
        json.dump(signup_data, file)

users = load_users_from_file()



def load_data(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

intent_data = load_data(r'Chikista.AI\data\intent_data.yml')
symptoms_data = load_data(r'Chikista.AI\data\symptoms_data.yml')
intents = intent_data.get('intents', [])

# Extract patterns and responses from intent data
intent_patterns_responses = [(intent.get('patterns', []), intent.get('responses', [])) for intent in intents]

# Flatten the list of patterns and responses
flattened_patterns_responses = [(pattern, response) for patterns, responses in intent_patterns_responses for pattern in patterns for response in responses]

# Extract symptoms from symptoms data
symptoms = [condition.get('symptom', '') for condition in symptoms_data.get('symptoms_data', [])]

# Flatten the list of symptoms
flattened_symptoms = [symptom.lower() for symptom in symptoms]

# Combine all data into a single list for vectorization
all_data = flattened_patterns_responses + flattened_symptoms

# Create a machine learning pipeline with TF-IDF vectorizer and a classifier (e.g., Naive Bayes)
model = make_pipeline(TfidfVectorizer(), MultinomialNB())

# Prepare the training data and labels
X_train = [data[0] for data in all_data]
y_train = [data[1] for data in all_data]

# Train the model
model.fit(X_train, y_train)

def respond_to_intent(user_input, intents, symptoms_data, enable_special_block=True):
    # Process user input with spaCy
    doc = nlp(user_input)
    predicted_response = model.predict([user_input])[0]
    
    for intent in intents:
        if 'symptom' in intent:
            symptom = intent['symptom']
            for pattern in intent['patterns']:
                if isinstance(pattern, str) and re.search(rf'\b{re.escape(pattern)}\b', user_input, re.IGNORECASE):
                    return get_symptom_info(symptom, symptoms_data)
        else:
            for pattern in intent['patterns']:
                if 'name' in intent and 'patterns' in intent:
                    if enable_special_block:
                        if any(token.lemma_ == pattern.lower() for token in doc if token.is_alpha):
                            return random.choice(intent['responses'])
                    if isinstance(pattern, str) and re.search(rf'\b{re.escape(pattern)}\b', user_input, re.IGNORECASE):
                        return random.choice(intent['responses'])
    else: 
        if isinstance(pattern, str) and re.search(rf'\b{re.escape(pattern)}\b', user_input, re.IGNORECASE):
            return predicted_response
              
    return random.choice(intents[-1]['responses'])



def get_symptom_info(symptom, symptoms_data):
    if not symptoms_data:
        return "I don't have information on that symptom. Please consult with a healthcare professional."

    for condition in symptoms_data.get('symptoms_data'):
        if condition.get('symptom') == symptom:
            response = f"{condition.get('description')}"
            return response

    return "I don't have information on that symptom. Please consult with a healthcare professional."


def is_authenticated():
    return 'user_id' in session

def authenticate_user(user_id, password):
    print(f"Attempting to authenticate user: {user_id}")

    if user_id in users:
        stored_password_hash = users[user_id].get('password_hash')
        print(f"Stored Password Hash: {stored_password_hash}")

        if check_password_hash(stored_password_hash, password):
            print("Authentication successful")
            session['user_id'] = user_id
            return True

    print("Authentication failed")
    return False


def save_signup_data(username, email, password):
    signup_data = load_signup_data_from_file()
    signup_data.append(f"Name: {username}\nGmail: {email}\nPassword: {password}\n\n")
    save_signup_data_to_file(signup_data)

def logout_user():
    session.pop('user_id', None)

# Routes...
@app.route('/')
def index():
    session.pop('user_id', None)
    if is_authenticated():
        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        with open('signup_data.txt', 'a') as file:
            file.write(f"Name - {username}\nGmail - {email}\nPassword - {password}\n\n")
        
        hashed_password = generate_password_hash(password)
        users[username] = {'password_hash': hashed_password}
        save_users_to_file(users)

        print(f"User {username} signed up successfully.")
        return redirect(url_for('index'))
    
    return render_template('index.html', mode=session.get('mode', 'signup'))

@app.route('/signup_data')
def signup_data():
    with open('signup_data.txt', 'r') as file:
        data = file.read()
    return render_template('signup_data.html', data=data)

# Routes for signin
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']

        if authenticate_user(user_id, password):
            return redirect(url_for('chat'))
        else:
            return render_template('index.html', error='Invalid credentials')
        
    return render_template('index.html', mode=session.get('mode', 'signin'))

# Route for chatbot interface
@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    print("Rendering chat.html")
    return render_template('chat.html')

@app.route('/chatbot', methods=['POST'])
def chatbot():
    if 'user_id' not in session:
        return jsonify({'response': 'Unauthorized'})
    user_input = request.form['user_input']
    response = respond_to_intent(user_input, intents, symptoms_data)
    return jsonify({'response': response})

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
