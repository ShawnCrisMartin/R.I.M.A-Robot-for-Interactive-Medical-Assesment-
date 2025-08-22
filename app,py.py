from flask import Flask, render_template, request, session, redirect, url_for
from Backend import initialize_patient, get_patient_reply
import csv
from datetime import datetime
import time
import uuid

app = Flask(__name__)
app.secret_key = "secret123"

# In-memory storage for user sessions (in production, use Redis or database)
user_sessions = {}

# File to store all user interactions
INTERACTIONS_FILE = "interactions.csv"

@app.route("/")
def landing():
    """Landing page that creates a new session and redirects to it"""
    # cleanup_old_sessions()
    session_id = str(uuid.uuid4())
    return redirect(url_for('index', session_id=session_id))

@app.route("/session/<session_id>", methods=["GET", "POST"])
def index(session_id):
    # Initialize patient and session variables if first visit
    if session_id not in user_sessions:
        disease_name, presenting_complaint, patient_symptoms = initialize_patient()
        user_sessions[session_id] = {
            "disease_name": disease_name,
            "presenting_complaint": presenting_complaint,
            "patient_symptoms": patient_symptoms,
            "chat": [
                "Patient: Hi doctor, I am not feeling well." # hidden disease
            ],
            "questions_left": 10,
            "created_at": time.time()
        }
        
        with open(INTERACTIONS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                session_id,
                "",
                "Patient: Hi doctor, I am not feeling well.",
                ""  # Diagnosis will be added later
            ])

    session_data = user_sessions[session_id]

    # if "questions_left" not in session:
    #     disease_name, presenting_complaint, patient_symptoms = initialize_patient()
    #     session["disease_name"] = disease_name
    #     session["presenting_complaint"] = presenting_complaint
    #     session["patient_symptoms"] = patient_symptoms

    
    #     session["chat"] = [
    #         "Patient: -"  # hidden disease
    #     ]
    #     session["questions_left"] = 10

    # Handle doctor question submissions
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

            # Log interaction to CSV
            with open(INTERACTIONS_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    session_id,
                    doctor_question,
                    reply,
                    ""  # Diagnosis will be added later
                ])

    return render_template(
        "index.html", 
        chat=session_data["chat"], 
        questions_left=session_data["questions_left"],
        session_id=session_id
    )

@app.route("/submit-diagnosis/<session_id>", methods=["POST"])
def submit_diagnosis(session_id):
    guess = request.form.get("diagnosis")
    correct = user_sessions[session_id]["disease_name"].lower()
    result = "pass" if guess and guess.lower() == correct else "fail"

    # Log the diagnosis to CSV
    with open(INTERACTIONS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            session_id,
            "",
            "",
            guess or "",
            user_sessions[session_id]["disease_name"]
        ])

    # Clear session for a fresh start
    session.clear()
    return f"<h2>You {result.upper()}ED!</h2><p>The correct diagnosis was: <strong>{correct.title()}</strong></p><a href='/'>Try Again</a>"

if __name__ == "__main__":
    app.run(debug=True, port=5005)
