from flask import Flask, request, jsonify
import google.generativeai as genai
import json
import os
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

# Function to clean and parse the response from Gemini
def clean_response_text(response_text):
    response_text = response_text.strip()

    if response_text.lower().startswith("```json"):
        response_text = response_text[7:].strip()
    if response_text.endswith("```"):
        response_text = response_text[:-3].strip()

    response_text = ''.join(char for char in response_text if char.isprintable())
    
    return response_text

# Function to analyze medical history text using Gemini
def analyze_medical_history(medical_history_text):
    prompt = f"""
    You are a medical record analyzer. Given the following patient medical history text, please extract and categorize the information in a structured JSON format.
    
    Medical History Text:
    {medical_history_text}
    
    Return the response in **exactly** this JSON structure, even if some fields are empty:
    {{
        "illnesses": [
            {{"condition": "name_of_condition"}}
        ],
        "surgeries": [
            {{"procedure": "name_of_surgery"}}
        ],
        "allergies": [
            {{"allergen": "name_of_allergen"}}
        ],
        "current_medications": [
            {{"medication": "name_of_medication"}}
        ]
    }}
    """
    try:
        response = model.generate_content(prompt)

        cleaned_response = clean_response_text(response.text)

        if not cleaned_response:
            print("Received empty or invalid response. Returning default structure.")
            return {
                "illnesses": [],
                "surgeries": [],
                "allergies": [],
                "current_medications": []
            }

        analyzed_data = json.loads(cleaned_response)
        
        if 'illnesses' not in analyzed_data:
            analyzed_data['illnesses'] = []
        if 'surgeries' not in analyzed_data:
            analyzed_data['surgeries'] = []
        if 'allergies' not in analyzed_data:
            analyzed_data['allergies'] = []
        if 'current_medications' not in analyzed_data:
            analyzed_data['current_medications'] = []

        return analyzed_data
    
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return {
            "illnesses": [],
            "surgeries": [],
            "allergies": [],
            "current_medications": []
        }
    except Exception as e:
        print(f"Error in analyzing medical history: {str(e)}")
        return {
            "illnesses": [],
            "surgeries": [],
            "allergies": [],
            "current_medications": []
        }

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

# API route to register or update patient
@app.route('/api/patient/register_or_update', methods=['POST'])
def register_or_update_patient():
    try:
        data = request.json
        
        # Ensure required fields are present
        required_personal_info = ['first_name', 'last_name', 'date_of_birth', 'gender', 'email', 'address']
        required_address_info = ['line1', 'line2', 'city', 'state', 'postcode']
        
        # Check if personal information is provided
        personal_information = data.get('personal_information', {})
        if not all(field in personal_information for field in required_personal_info):
            return jsonify({
                "status": "error",
                "message": "Missing required personal information"
            }), 400
        
        # Check if address information is complete
        address = personal_information.get('address', {})
        if not all(field in address for field in required_address_info):
            return jsonify({
                "status": "error",
                "message": "Incomplete address information"
            }), 400

        email = personal_information.get('email')
        if not email:
            return jsonify({
                "status": "error",
                "message": "Email is required to identify the patient"
            }), 400

        # Check if the patient exists based on email
        existing_patient = next((patient for patient in patients_db.values() if patient['personal_information']['email'] == email), None)

        if existing_patient:
            # If a patient with the provided email exists, update their details
            patient_id = existing_patient['patient_id']
            print(f"Updating patient with patient ID: {patient_id}")

            # Create a new patient_info object from the request data
            patient_info = existing_patient.copy()

            # Store old data for comparison
            old_data = existing_patient.copy()

            # Update personal information (excluding email, handled by front-end)
            patient_info['personal_information'] = personal_information
            patient_info['demographic_information'] = data.get('demographic_information', {})

            # Update medical history if provided
            if 'medical_history' in data:
                patient_info['medical_history'] = analyze_medical_history(data['medical_history'])

            # Save the updated patient record
            updated_patient = save_patient(patient_info, patient_id)
            
            # Get the list of updated fields
            updated_fields = get_updated_fields(old_data, updated_patient)
            
            return jsonify({
                "status": "success",
                "message": "Patient record updated successfully",
                "updates": updated_fields,
                "data": {
                    "patient_info": updated_patient
                }
            }), 200

        else:
            # If the patient doesn't exist, create a new patient record
            print(f"Registering new patient with email: {email}")

            # Create the patient_info dictionary from the request data
            patient_info = {
                "personal_information": personal_information,
                "demographic_information": data.get('demographic_information', {}),
                "medical_history": analyze_medical_history(data.get('medical_history', ''))
            }

            # Save the new patient record
            new_patient = save_patient(patient_info)
            
            return jsonify({
                "status": "success",
                "message": f"New patient record created successfully for {personal_information['first_name']} {personal_information['last_name']}",
                "data": {
                    "patient_info": new_patient
                }
            }), 201

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


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