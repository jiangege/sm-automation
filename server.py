import os
from flask import Flask, request, render_template, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from sm_auto import SuperMemoAutomation
from dotenv import load_dotenv

load_dotenv()

auth = HTTPBasicAuth()

app = Flask(__name__)
app.debug = True
sm = SuperMemoAutomation('sm19.exe')


@auth.verify_password
def verify_password(username, password):
    env_username = os.getenv('MY_APP_USERNAME')
    env_password = os.getenv('MY_APP_PASSWORD')

    if username == env_username and password == env_password:
        return True
    return False


@app.route('/')
@auth.login_required
def home():
    current_element = sm.get_current_element()
    status = sm.get_status()
    return render_template('index.html', current_element=current_element,  status=status, is_next_enabled=sm.is_next_enabled, is_prev_enabled=sm.is_prev_enabled)


@app.route('/get_current_element', methods=['GET'])
@auth.login_required
def get_current_element():
    return sm.get_current_element()


@app.route('/action/<type>', methods=['POST'])
@auth.login_required
def execute_action(type):
    actions = ['learn', 'next', 'show_answer']
    if type in actions:
        method = getattr(sm, type, None)
        if method is not None and callable(method):
            method()
        else:
            return {"error": f"Method {type} not found or not callable."}, 404
    else:
        return {"error": "Invalid action type."}, 400
    return redirect(url_for('home'))


@app.route('/grade', methods=['POST'])
@auth.login_required
def grade():
    rating = request.form.get('rating')
    if rating is not None:
        sm.grade(int(rating))
    else:
        return {"error": "No rating provided."}, 400
    return redirect(url_for('home'))


@app.route('/set_priority', methods=['POST'])
@auth.login_required
def set_priority():
    priority = request.json.get('priority')
    if priority is not None:
        try:
            sm.set_priority(int(priority))
        except Exception as e:
            return {"error": "Failed to set priority. Reason: " + str(e)}, 500
    else:
        return {"error": "No priority provided."}, 400
    return redirect(url_for('home'))


@app.route('/edit/<type>', methods=['POST'])
@auth.login_required
def edit(type):
    # Extract the content and other data from the request's JSON body
    data = request.get_json()
    content = data.get('content')

    if type == 'html':
        sm.set_html_content(htm_file=data.get('htmFile'), content=content)
    elif type == 'text':
        sm.set_text_content(component_index=data.get('index'), content=content)
    else:
        return {"error": "Invalid type."}, 400

    return {"message": "Content successfully updated."}, 200


@app.route('/prev_element', methods=['POST'])
@auth.login_required
def prev_element():
    try:
        sm.prev_element()
    except Exception as e:
        return {"error": "Failed to go to the previous element. Reason: " + str(e)}, 500

    return redirect(url_for('home'))


@app.route('/next_element', methods=['POST'])
@auth.login_required
def next_element():
    try:
        sm.next_element()
    except Exception as e:
        return {"error": "Failed to go to the next element. Reason: " + str(e)}, 500

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')
