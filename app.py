from flask import Flask, request, jsonify
import google.generativeai as genai
import json
import os
from llm_analyzer import analyze_medical_history, analyze_personal_info, analyze_demographic_info
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Simulating a simple in-memory database for patients
patients_db = {}
patient_id_counter = 1

def get_updated_fields(old_data, new_data):
    """Compare old and new data to identify updated fields"""
    updates = {}
    
    if not old_data:
        return {"all": "New patient record created"}
        
    for category in ['personal_information', 'demographic_information', 'medical_history']:
        if category in new_data and category in old_data:
            if new_data[category] != old_data[category]:
                updates[category] = {
                    k: new_data[category][k]
                    for k in new_data[category]
                    if k not in old_data[category] or new_data[category][k] != old_data[category][k]
                }
    
    return updates

# Function to save or update patient
def save_patient(patient_info, patient_id=None):
    global patient_id_counter
    
    if patient_id:
        # Update the existing patient
        patients_db[patient_id] = patient_info
    else:
        # Assign new patient ID (incremental)
        patient_id = patient_id_counter
        patient_id_counter += 1
        patient_info['patient_id'] = patient_id
        patients_db[patient_id] = patient_info
    
    return patients_db[patient_id]

# API route to analyze personal information
@app.route('/api/patient/analyze_personal_info', methods=['POST'])
def analyze_personal_info_api():
    try:
        # Get the personal information text from the request body
        data = request.json
        personal_info_text = data.get('personal_info', '')
        
        if not personal_info_text:
            return jsonify({
                "status": "error",
                "message": "Personal information text is required"
            }), 400

        # Analyze the personal information text
        personal_info_data = analyze_personal_info(personal_info_text)

        # Construct the response with the required format
        response = {
            "status": "success",
            "message": "Personal information analyzed successfully",
            "personal_information": {
                "personal_info_text": personal_info_text,
                "personal_info_data": personal_info_data
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
        

#API route for demographic information analysis      
@app.route('/api/patient/analyze_demographic_info', methods=['POST'])
def analyze_demographic_info_api():
    try:
        # Get demographic information text from the request body
        data = request.json
        demographic_info_text = data.get('demographic_info', '')

        if not demographic_info_text:
            return jsonify({
                "status": "error",
                "message": "Demographic information text is required"
            }), 400

        # Analyze the demographic information
        demographic_info_data = analyze_demographic_info(demographic_info_text)

        # Construct the response
        response = {
            "status": "success",
            "message": "Demographic information analyzed successfully",
            "demographic_information": {
                "demographic_info_text": demographic_info_text,
                "demographic_info_data": demographic_info_data
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# API route to analyze medical history text
@app.route('/api/patient/analyze_medical_history', methods=['POST'])
def analyze_medical_history_api():
    try:
        # Get the medical history text from the request body
        data = request.json
        medical_history_text = data.get('medical_history', '')
        
        if not medical_history_text:
            return jsonify({
                "status": "error",
                "message": "Medical history text is required"
            }), 400

        # Analyze the medical history text
        medical_history_data = analyze_medical_history(medical_history_text)

        # Construct the response with the required format
        response = {
            "status": "success",
            "message": "Medical history analyzed successfully",
            "medical_information": {
                "medical_history_text": medical_history_text,
                "medical_history_data": medical_history_data
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=9000)