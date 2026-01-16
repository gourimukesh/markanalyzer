from google import genai
from google.genai import types
import json, tempfile, os, time, streamlit as st

# Secure API Key Loading
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "AIzaSyB5n6a94jgEaLDfeKLLrudDBskJyynpeV0" # For local testing only

client = genai.Client(api_key=API_KEY)

def process_ai_analysis(marks_pdf, question_pdf=None):
    model_id = "gemini-2.0-flash-lite"
    files_to_send = []
    
    try:
        # Check if we are in Mode 2
        is_mode_2 = question_pdf is not None
        
        for pdf in filter(None, [marks_pdf, question_pdf]):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf.getvalue())
                tmp_path = tmp.name
            uploaded_file = client.files.upload(file=tmp_path)
            while uploaded_file.state == "PROCESSING":
                time.sleep(1)
                uploaded_file = client.files.get(name=uploaded_file.name)
            files_to_send.append(uploaded_file)
            os.remove(tmp_path)

        prompt = """
        Analyze student data and return JSON with root key "students".
        
        MODE 1 (General): Extract name, marks (dict), percentage, strong_subjects, weak_subjects.
        
        MODE 2 (Deep Dive - only if 2nd PDF provided): Also extract q_marks (question-wise), 
        mistake_type (Must be: 'Concept error', 'Calculation mistake', or 'Formula error'),
        weak_topics (list), and improvement suggestions.
        """

        response = client.models.generate_content(
            model=model_id,
            contents=[prompt] + files_to_send,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        
        for f in files_to_send:
            client.files.delete(name=f.name)
            
        return json.loads(response.text)
        
    except Exception as e:
        return {"error": str(e)}