import os
from flask import Flask, request, render_template
import fitz  # PyMuPDF
import spacy
from nltk.corpus import wordnet
import re

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Get synonyms using WordNet
def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().lower().replace("_", " "))
    return synonyms

# Extract keywords from any job description using NLP
def extract_job_keywords(text):
    doc = nlp(text.lower())
    keywords = set()
    for token in doc:
        if token.pos_ in ['NOUN', 'PROPN'] or token.ent_type_ in ['SKILL', 'ORG', 'PRODUCT']:
            if not token.is_stop and token.is_alpha:
                keywords.add(token.text.strip())
    print("📌 Extracted Job Keywords:", keywords)  # Debug print
    return list(keywords)

# Extract skills from resume and match with job description
def extract_skills(resume_text, job_description_keywords):
    resume_text = resume_text.lower()
    print("📄 Resume Text (First 500 chars):", resume_text[:500])  # Debug print
    doc = nlp(resume_text)

    extracted_skills = set()
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "SKILL"]:
            extracted_skills.add(ent.text.lower())

    for token in doc:
        if token.text.lower() in job_description_keywords:
            extracted_skills.add(token.text.lower())

    print("🧠 Extracted Resume Skills:", extracted_skills)  # Debug print

    matching_skills = []
    for jd_keyword in job_description_keywords:
        if jd_keyword in extracted_skills:
            matching_skills.append(jd_keyword)
        else:
            synonyms = get_synonyms(jd_keyword)
            if any(skill in extracted_skills for skill in synonyms):
                matching_skills.append(jd_keyword)

    percentage = (len(matching_skills) / len(job_description_keywords)) * 100 if job_description_keywords else 0
    print("✅ Matching Skills:", matching_skills)  # Debug print
    print("📊 Matching Percentage:", percentage)   # Debug print

    return matching_skills, percentage

# Extract resume text
def extract_resume_text(file):
    text = ""
    pdf = fitz.open(stream=file.read(), filetype="pdf")
    for page in pdf:
        text += page.get_text()
    pdf.close()
    return text

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files:
        print("🚫 No file uploaded.")
        return "No file uploaded", 400

    file = request.files['resume']
    job_text = request.form['job_description']

    print("📥 Job Description Received:", job_text)

    job_keywords = extract_job_keywords(job_text)

    if file and file.filename.endswith('.pdf'):
        try:
            print("📁 Uploaded Resume:", file.filename)
            resume_text = extract_resume_text(file)

            skills, percentage = extract_skills(resume_text, job_keywords)

            return render_template("result.html", skills=skills, percentage=percentage)
        except Exception as e:
            print("🔥 Error while analyzing:", str(e))
            return f"Error: {str(e)}", 400
    else:
        print("❗ Invalid file format. Only PDF allowed.")
        return "Please upload a PDF file.", 400

if __name__ == '__main__':
    print("🚀 Flask server starting on http://127.0.0.1:5000 ...")
    app.run(debug=True)
