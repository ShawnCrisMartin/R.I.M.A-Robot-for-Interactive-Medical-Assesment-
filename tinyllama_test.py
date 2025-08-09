from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import sqlite3
import random

# Load TinyLlama
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
# Load model onto GPU
model = AutoModelForCausalLM.from_pretrained(model_name).to('cuda')

# Connect to database
conn = sqlite3.connect("patients.db")
cursor = conn.cursor()

# Pick random disease
cursor.execute("SELECT id, name, presenting_complaint FROM diseases ORDER BY RANDOM() LIMIT 1")
disease_row = cursor.fetchone()
disease_id, disease_name, presenting_complaint = disease_row

# Fetch associated symptoms
cursor.execute("SELECT symptom, description FROM symptoms WHERE disease_id = ?", (disease_id,))
symptom_rows = cursor.fetchall()
patient_symptoms = {symptom: desc for symptom, desc in symptom_rows}

# Known symptom keywords
common_symptoms = ["fever", "cough", "headache", "chest pain", "shortness of breath", "fatigue", "nausea", "dizziness", "abdominal pain"]

# Patient Intro
print("🩺 RIMA AI Patient Simulator (SQL powered)\n")
print(f"Patient: Hi, I'm a patient with {disease_name}.")
print(f"Patient: {presenting_complaint}\n")
print("Type 'exit' to end the consultation.\n")

# Interaction loop
while True:
    doctor_question = input("Doctor: ")

    if doctor_question.lower() == "exit":
        print("Patient: Thank you, doctor.")
        break

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
        # AI for unrelated conversations
        prompt = f"""
You are a patient diagnosed with {disease_name}.
Your presenting complaint is: "{presenting_complaint}"
Your symptoms are: {', '.join(patient_symptoms.keys())}

If the doctor's question is unrelated, reply naturally like "I'm not sure." or "No, nothing like that."

Doctor: {doctor_question}
Patient:"""

        # Tokenize and move inputs to GPU
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to('cuda') for k, v in inputs.items()}

        outputs = model.generate(
            **inputs,
            max_new_tokens=250,
            repetition_penalty=1.2,
            do_sample=True,
            temperature=0.7
        )

        reply = tokenizer.decode(outputs[0], skip_special_tokens=True)

        if "Patient:" in reply:
            response = reply.split("Patient:")[-1].strip().split("\n")[0]
        else:
            response = reply.strip()

    print(f"Patient: {response}\n")

conn.close()
