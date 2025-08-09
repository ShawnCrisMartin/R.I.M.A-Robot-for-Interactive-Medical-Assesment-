from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import sqlite3
import random

model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
# model_name = "mistralai/Mistral-7B-Instruct-v0.3"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name).to('cuda')

def initialize_patient():
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, presenting_complaint FROM diseases ORDER BY RANDOM() LIMIT 1")
    disease_row = cursor.fetchone()
    disease_id, disease_name, presenting_complaint = disease_row

    cursor.execute("SELECT symptom, description FROM symptoms WHERE disease_id = ?", (disease_id,))
    symptom_rows = cursor.fetchall()
    patient_symptoms = {symptom: desc for symptom, desc in symptom_rows}

    conn.close()
    return disease_name, presenting_complaint, patient_symptoms

def get_patient_reply(disease_name, presenting_complaint, patient_symptoms, doctor_question):
    common_symptoms = ["fever", "cough", "headache", "chest pain", "shortness of breath", "fatigue", "nausea", "dizziness", "abdominal pain"]

    for symptom in patient_symptoms:
        if symptom.lower() in doctor_question.lower():
            return patient_symptoms[symptom]

    for word in common_symptoms:
        if word in doctor_question.lower():
            return "No, I haven't experienced that."

    prompt = f"""
You are a patient diagnosed with {disease_name}.
Your presenting complaint is: "{presenting_complaint}"
Your symptoms are: {', '.join(patient_symptoms.keys())}

If the doctor's question is unrelated, reply naturally like "I'm not sure." or "No, nothing like that."

Doctor: {doctor_question}
Patient:"""

    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to('cuda') for k, v in inputs.items()}

    outputs = model.generate(
        **inputs,
        max_new_tokens=500,
        repetition_penalty=1.2,
        do_sample=True,
        temperature=0.7
    )

    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if "Patient:" in reply:
        return reply.split("Patient:")[-1].strip().split("\n")[0]
    return reply.strip()
