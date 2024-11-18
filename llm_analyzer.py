
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Function to clean and parse the response from Gemini 
def clean_response_text(response_text):
    response_text = response_text.strip()

    if response_text.lower().startswith("```json"):
        response_text = response_text[7:].strip()
    if response_text.endswith("```"):
        response_text = response_text[:-3].strip()

    response_text = ''.join(char for char in response_text if char.isprintable())
    
    return response_text


#Function to call personal information text using LLM 
def analyze_personal_info(personal_info_text: str) -> dict:
    """Analyze personal information text and return structured data."""
    prompt = f"""
    You are a patient registration information analyzer. Given the following patient personal information text, please extract and structure the information in a JSON format.

    If the text is irrelevant or does not resemble valid personal information, respond with:
    "Sorry, I don't have an answer for this question."

    Personal Information Text:
    {personal_info_text}

    Return the response in **exactly** this JSON structure:
    {{
            "name": {{
                "first_name": "",
                "middle_name": "",
                "last_name": ""
            }},
            "address": {{
                "line1": "",
                "line2": "",
                "city": "",
                "state": "",
                "zip": ""
            }},
            "contact_info": {{
                "email": "",
                "phone": ""
            }},
            "specifications": {{
                "gender": "",
                "date_of_birth": ""
            }}
    }}
    """
    try:
        response = model.generate_content(prompt)
        cleaned_response = clean_response_text(response.text)

        # Parse the JSON response
        analyzed_data = json.loads(cleaned_response)

        # Ensure no dummy values exist; replace them with defaults
        default_structure = {
            "name": {"first_name": "", "middle_name": "", "last_name": ""},
            "address": {"line1": "", "line2": "", "city": "", "state": "", "zip": ""},
            "contact_info": {"email": "", "phone": ""},
            "specifications": {"gender": "", "date_of_birth": ""}
        }

        # Recursive function to sanitize and enforce defaults
        def sanitize(data, defaults):
            if isinstance(defaults, dict):
                return {key: sanitize(data.get(key, ""), value) for key, value in defaults.items()}
            if isinstance(defaults, list):
                return data if isinstance(data, list) else []
            return data if data and not isinstance(data, str) or data.strip() else ""

        return sanitize(analyzed_data, default_structure)

    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return {
            "name": {"first_name": "", "middle_name": "", "last_name": ""},
            "address": {"line1": "", "line2": "", "city": "", "state": "", "zip": ""},
            "contact_info": {"email": "", "phone": ""},
            "specifications": {"gender": "", "date_of_birth": ""}
        }
    except Exception as e:
        print(f"Error in analyzing personal information: {str(e)}")
        return {
            "name": {"first_name": "", "middle_name": "", "last_name": ""},
            "address": {"line1": "", "line2": "", "city": "", "state": "", "zip": ""},
            "contact_info": {"email": "", "phone": ""},
            "specifications": {"gender": "", "date_of_birth": ""}
        }

#def analyze_personal_info(personal_info_text: str) -> dict:
    """Analyze personal information text and return structured data"""
    prompt = f"""
    You are a patient registration information analyzer. Given the following patient personal information text, please extract and structure the information in a JSON format.
    
    If the text is irrelevant or does not resemble valid personal information, respond with:
"Sorry, I don't have an answer for this question."
    
    Personal Information Text:
    {personal_info_text}
    
    Return the response in **exactly** this JSON structure:
    {{
            "name": {{
                "first_name": "patient_first_name",
                "middle_name": "patient_middle_name",
                "last_name": "patient_last_name"
            }},
            "address": {{
                "line1": "street_address_line1",
                "line2": "street_address_line2",
                "city": "city_name",
                "state": "state_name",
                "zip": "zip_code"
            }},
            "contact_info": {{
                "email": "email_address",
                "phone": "phone_number"
            }},
            "specifications": {{
                "gender": "patient_gender",
                "date_of_birth": "YYYY-MM-DD"
            }}
        }}
    """
    
    try:
        response = model.generate_content(prompt)
        cleaned_response = clean_response_text(response.text)
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"Error in analyzing personal information: {str(e)}")
        return {}

# Function to analyze medical history text using LLM
def analyze_medical_history(medical_history_text):
    prompt = f"""
    You are a medical record analyzer. Given the following patient medical history text, please extract and categorize the information in a structured JSON format.
    If the text is irrelevant or does not resemble valid personal information, respond with:
    "Sorry, I don't have an answer for this question."

    If the information is missing, leave it empty.
    
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
        
        
# Function to analyze demographic information text using LLM
def analyze_demographic_info(demographic_info_text):
    prompt = f"""
    You are a healthcare provider demographic information analyzer. Given the following text, please extract and structure demographic information such as marital status, occupation, ethnicity, and preferred language.
    If the text is irrelevant or does not resemble valid personal information, respond with:
"Sorry, I don't have an answer for this question."

    If the information is missing, leave it empty. For "preferred_language", return an array of languages if multiple languages are mentioned.

    Input Text:
    {demographic_info_text}

    Return the response in **exactly** this JSON structure:
    {{
        "marital_status": "patient_marital_status",
        "occupation": "patient_occupation",
        "ethnicity": "patient_ethnicity",
        "preferred_language": ["list_of_languages"]
    }}
    """
    try:
        response = model.generate_content(prompt)
        cleaned_response = clean_response_text(response.text)

        # Return default values if the response is empty or invalid
        if not cleaned_response:
            print("Received empty or invalid response. Returning default structure.")
            return {
                "marital_status": "",
                "occupation": "",
                "ethnicity": "",
                "preferred_language": []
            }

        analyzed_data = json.loads(cleaned_response)

        # Ensure all keys are present
        for key in ["marital_status", "occupation", "ethnicity", "preferred_language"]:
            if key not in analyzed_data:
                if key == "preferred_language":
                    analyzed_data[key] = []
                else:
                    analyzed_data[key] = ""

        return analyzed_data

    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return {
            "marital_status": "",
            "occupation": "",
            "ethnicity": "",
            "preferred_language": []
        }
    except Exception as e:
        print(f"Error in analyzing demographic information: {str(e)}")
        return {
            "marital_status": "",
            "occupation": "",
            "ethnicity": "",
            "preferred_language": []
        }