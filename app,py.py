from flask import Flask, render_template, request, session, redirect, url_for
from model_backend import initialize_patient, get_patient_reply

app = Flask(__name__)
app.secret_key = "secret123"

@app.route("/", methods=["GET", "POST"])
def index():
    if "questions_left" not in session:
        disease_name, presenting_complaint, patient_symptoms = initialize_patient()
        session["disease_name"] = disease_name
        session["presenting_complaint"] = presenting_complaint
        session["patient_symptoms"] = patient_symptoms
        session["chat"] = [
            f"Patient: Hi, I'm a patient with {disease_name}.",
            f"Patient: {presenting_complaint}"
        ]
        session["questions_left"] = 10

    if request.method == "POST":
        doctor_question = request.form["question"]
        if session["questions_left"] > 0:
            session["questions_left"] -= 1
            reply = get_patient_reply(
                session["disease_name"],
                session["presenting_complaint"],
                session["patient_symptoms"],
                doctor_question
            )
            session["chat"].append(f"Doctor: {doctor_question}")
            session["chat"].append(f"Patient: {reply}")

    return render_template("index.html", chat=session["chat"], questions_left=session["questions_left"])

@app.route("/submit-diagnosis", methods=["POST"])
def submit_diagnosis():
    guess = request.form["diagnosis"]
    correct = session["disease_name"].lower()
    result = "pass" if guess.lower() == correct else "fail"
    session.clear()
    return f"<h2>You {result.upper()}ED!</h2><a href='/'>Try Again</a>"

if __name__ == "__main__":
    app.run(debug=True)
