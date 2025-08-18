from flask import Flask, render_template, request, session
from Backend import initialize_patient, get_patient_reply
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# File to store all user interactions
INTERACTIONS_FILE = "interactions.csv"

@app.route("/", methods=["GET", "POST"])
def index():
    # Initialize patient and session variables if first visit
    if "questions_left" not in session:
        disease_name, presenting_complaint, patient_symptoms = initialize_patient()
        session["disease_name"] = disease_name
        session["presenting_complaint"] = presenting_complaint
        session["patient_symptoms"] = patient_symptoms

    
        session["chat"] = [
            "Patient: -"  # hidden disease
        ]
        session["questions_left"] = 10

    # Handle doctor question submissions
    if request.method == "POST":
        doctor_question = request.form.get("question")
        if doctor_question and session["questions_left"] > 0:
            session["questions_left"] -= 1

            # Generate patient reply using the real disease internally
            reply = get_patient_reply(
                session["disease_name"],
                session["presenting_complaint"],
                session["patient_symptoms"],
                doctor_question
            )

            # Add messages to chat
            session["chat"].append(f"Doctor: {doctor_question}")
            session["chat"].append(f"Patient: {reply}")

            # Log interaction to CSV
            with open(INTERACTIONS_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    doctor_question,
                    reply,
                    ""  # Diagnosis will be added later
                ])

    return render_template(
        "index.html",
        chat=session.get("chat", []),
        questions_left=session.get("questions_left", 0)
    )

@app.route("/submit-diagnosis", methods=["POST"])
def submit_diagnosis():
    guess = request.form.get("diagnosis")
    correct = session.get("disease_name", "").lower()
    result = "pass" if guess and guess.lower() == correct else "fail"

    # Log the diagnosis to CSV
    with open(INTERACTIONS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            "",
            "",
            guess or ""
        ])

    # Clear session for a fresh start
    session.clear()
    return f"<h2>You {result.upper()}ED!</h2><a href='/'>Try Again</a>"

if __name__ == "__main__":
    app.run(debug=True)
