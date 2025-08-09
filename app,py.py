from flask import Flask, render_template, request, redirect, url_for
from model_backend import initialize_patient, get_patient_reply
import uuid
import time

app = Flask(__name__)

# In-memory storage for user sessions (in production, use Redis or database)
user_sessions = {}

# Clean up old sessions (older than 1 hour)
def cleanup_old_sessions():
    current_time = time.time()
    sessions_to_remove = []
    for session_id, session_data in user_sessions.items():
        if current_time - session_data.get('created_at', 0) > 3600:  # 1 hour
            sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        del user_sessions[session_id]

@app.route("/")
def landing():
    """Landing page that creates a new session and redirects to it"""
    cleanup_old_sessions()
    session_id = str(uuid.uuid4())
    return redirect(url_for('index', session_id=session_id))

@app.route("/session/<session_id>", methods=["GET", "POST"])
def index(session_id):
    # Initialize session if it doesn't exist
    if session_id not in user_sessions:
        disease_name, presenting_complaint, patient_symptoms = initialize_patient()
        user_sessions[session_id] = {
            "disease_name": disease_name,
            "presenting_complaint": presenting_complaint,
            "patient_symptoms": patient_symptoms,
            "chat": [
                f"Patient: Hi, I'm a patient with {disease_name}.",
                f"Patient: {presenting_complaint}"
            ],
            "questions_left": 10,
            "created_at": time.time()
        }

    session_data = user_sessions[session_id]

    if request.method == "POST":
        doctor_question = request.form["question"]
        if session_data["questions_left"] > 0:
            session_data["questions_left"] -= 1
            reply = get_patient_reply(
                session_data["disease_name"],
                session_data["presenting_complaint"],
                session_data["patient_symptoms"],
                doctor_question
            )
            session_data["chat"].append(f"Doctor: {doctor_question}")
            session_data["chat"].append(f"Patient: {reply}")

    return render_template("index.html", 
                         chat=session_data["chat"], 
                         questions_left=session_data["questions_left"],
                         session_id=session_id)

@app.route("/submit-diagnosis/<session_id>", methods=["POST"])
def submit_diagnosis(session_id):
    if session_id not in user_sessions:
        return redirect(url_for('landing'))
    
    guess = request.form["diagnosis"]
    correct = user_sessions[session_id]["disease_name"].lower()
    result = "pass" if guess.lower() == correct else "fail"
    
    # Clean up this session
    del user_sessions[session_id]
    
    return f"<h2>You {result.upper()}ED!</h2><p>The correct diagnosis was: <strong>{correct.title()}</strong></p><a href='/'>Try Again</a>"

if __name__ == "__main__":
    app.run(debug=True, port=5005)
