from flask import Flask, request, jsonify, render_template
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import sqlite3

app = Flask(__name__)

# Load model/tokenizer once at startup
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Connect to DB once
conn = sqlite3.connect("patients.db", check_same_thread=False)
cursor = conn.cursor()

# Pick random disease and symptoms once at startup
cursor.execute("SELECT id, name, presenting_complaint FROM diseases ORDER BY RANDOM() LIMIT 1")
disease_id, disease_name, presenting_complaint = cursor.fetchone()

cursor.execute("SELECT symptom, description FROM symptoms WHERE disease_id = ?", (disease_id,))
patient_symptoms = {symptom: desc for symptom, desc in cursor.fetchall()}

common_symptoms = ["fever", "cough", "headache", "chest pain", "shortness of breath", "fatigue", "nausea", "dizziness", "abdominal pain"]

@app.route("/")
def index():
    return render_template("index.html", disease_name=disease_name, presenting_complaint=presenting_complaint)

@app.route("/chat", methods=["POST"])
def chat():
    doctor_question = request.json.get("question", "").strip()

    if doctor_question.lower() == "exit":
        return jsonify(response="Thank you, doctor.")

    matched_symptom = None
    mentioned_symptom = None

    for symptom in patient_symptoms:
        if symptom.lower() in doctor_question.lower():
            matched_symptom = symptom
            break

    for word in common_symptoms:
        if word in doctor_question.lower():
            mentioned_symptom = word
            break

    if matched_symptom:
        response = patient_symptoms[matched_symptom]
    elif mentioned_symptom:
        response = "No, I haven't experienced that."
    else:
        prompt = f"""
You are a patient diagnosed with {disease_name}.
Your presenting complaint is: "{presenting_complaint}"
Your symptoms are: {', '.join(patient_symptoms.keys())}

If the doctor's question is unrelated, reply naturally like "I'm not sure." or "No, nothing like that."

Doctor: {doctor_question}
Patient:"""

        inputs = tokenizer(prompt, return_tensors="pt")

        outputs = model.generate(
            **inputs,
            max_new_tokens=50,
            repetition_penalty=1.2,
            do_sample=True,
            temperature=0.7
        )

        reply = tokenizer.decode(outputs[0], skip_special_tokens=True)

        if "Patient:" in reply:
            response = reply.split("Patient:")[-1].strip().split("\n")[0]
        else:
            response = reply.strip()

    return jsonify(response=response)

if __name__ == "__main__":
    app.run(debug=True)
