import os
import re
import io
import pdfrw
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from flask import Flask, render_template, request, redirect, url_for


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_text(filepath):
    with open(filepath, 'rb') as f:
        resource_manager = PDFResourceManager()
        output_stream = io.StringIO()
        device = TextConverter(resource_manager, output_stream, laparams=None)
        interpreter = PDFPageInterpreter(resource_manager, device)

        for page in PDFPage.get_pages(f, check_extractable=True):
            interpreter.process_page(page)

        text = output_stream.getvalue()

        device.close()
        output_stream.close()

        return text

def extract_info(text):
    
    name_pattern = r"(?i)\b(?:name|full name|candidate name)\b[:\-\s]*(\w+(?:\s+\w+)+)"
    name_match = re.search(name_pattern, text)
    name = name_match.group(1) if name_match else None

    
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    email_match = re.search(email_pattern, text)
    email = email_match.group(0) if email_match else None

    
    phone_pattern = r"(?i)\b(?:phone|mobile|contact)\b[:\-\s]*(\d{10})"
    phone_match = re.search(phone_pattern, text)
    phone = phone_match.group(1) if phone_match else None

    
    jee_pattern = r"(?i)\b(?:jee\s*(?:main|advanced)?\s*score|jee\s*(?:main|advanced)?)\b[:\-\s]*(\d+(?:\.\d+)?)"
    jee_match = re.search(jee_pattern, text)
    jee_score = float(jee_match.group(1)) if jee_match else None

    # Calculate scholarship amount based on JEE Mains score
    scholarship_amount = None
    if jee_score is not None and jee_score >= 270:
        scholarship_amount = 10000
    elif jee_score is not None and jee_score >= 210:
        scholarship_amount = 5000


    sports_keywords = ['sport', 'athletic', 'football', 'basketball', 'cricket', 'tennis']
    sports_pattern = r"(?i)\b({})\b".format("|".join(sports_keywords))
    sports_match = re.search(sports_pattern, text)
    sports_scholarship_amount = 5000 if sports_match else None    

    return name, email, phone, jee_score, scholarship_amount,sports_scholarship_amount


@app.route('/')
def index():
    return render_template('form.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    
    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        if filename.endswith('.pdf'):
            text = extract_text(filepath)
        elif filename.endswith('.txt'):
            with open(filepath, 'r') as f:
                text = f.read()
        else:
            return redirect(request.url)              
        name, email, phone, jee_score, scholarship_amount, sports_scholarship_amount = extract_info(text)
        return render_template('uploaded.html', filename=filename, name=name, email=email, phone=phone, jee_score=jee_score, scholarship_amount=scholarship_amount, sports_scholarship_amount=sports_scholarship_amount)
    else:
        return redirect(request.url)






if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
