import fitz, spacy, os, re, google.generativeai as genai
from flask import Flask, request, render_template

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")
genai.configure(api_key="AIzaSyD3IjuxzePlOnBAxMZMzsWgk9ismhPerTA")

TECHNICAL_SKILLS = {"Python", "C", "C++", "Java", "SQL", "Machine Learning", "Deep Learning", "AI", "NLP", "TensorFlow", "PyTorch", "Cloud", "AWS", "Kubernetes", "JavaScript", "HTML", "CSS", "Flask", "Django", "Docker", "Git"}
TOP_UNIVERSITIES = {"Stanford", "MIT", "Harvard", "UC Berkeley", "Carnegie Mellon", "IIT", "NIT", "BITS", "IIIT"}
DEGREE_KEYWORDS = {"Bachelor", "Master", "PhD", "B.Tech", "M.Tech", "M.Sc", "B.Sc", "BE", "ME", "MBA", "MCA", "BCA", "Diploma"}

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()

def extract_resume_details(text):
    doc = nlp(text)
    skills, experience, education = set(), set(), set()
    for word in TECHNICAL_SKILLS:
        if re.search(rf"\b{word}\b", text, re.IGNORECASE):
            skills.add(word)
    for ent in doc.ents:
        text_cleaned = ent.text.strip()
        if ent.label_ in ["ORG", "PERSON", "GPE"]:
            if any(title in text_cleaned.lower() for title in ["intern", "engineer", "developer", "manager", "lead", "analyst"]):
                experience.add(text_cleaned)
        if any(degree in text_cleaned for degree in DEGREE_KEYWORDS) or text_cleaned in TOP_UNIVERSITIES:
            education.add(text_cleaned)
    return list(skills), list(experience), list(education)

def score_resume(skills, experience, education):
    skill_weight, experience_weight, education_weight, research_weight, leadership_weight = 40, 30, 15, 10, 5
    skill_score = (sum(1 for skill in skills if skill in TECHNICAL_SKILLS) / len(TECHNICAL_SKILLS)) * skill_weight if TECHNICAL_SKILLS else 0
    experience_score = min(len(experience) * 5, experience_weight)
    education_score = min(sum(10 if edu in TOP_UNIVERSITIES else 5 for edu in education), education_weight)
    research_score = research_weight if any("research" in exp.lower() for exp in experience) else 0
    leadership_score = leadership_weight if any("lead" in exp.lower() or "manager" in exp.lower() for exp in experience) else 0
    return round(min(skill_score + experience_score + education_score + research_score + leadership_score, 100))

def generate_summary_gemini(resume_text):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(f"Summarize this resume professionally for a recruiter:\n\n{resume_text}")
    return response.text if response else "Summary generation failed."

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["resume"]
        if file:
            file_path = "uploaded_resume.pdf"
            file.save(file_path)
            resume_text = extract_text_from_pdf(file_path)
            skills, experience, education = extract_resume_details(resume_text)
            score = score_resume(skills, experience, education)
            summary = generate_summary_gemini(resume_text)
            return render_template("result.html", skills=skills, experience=experience, education=education, score=score, summary=summary)
    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True)
