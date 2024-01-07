from flask import Flask, render_template, request, redirect, url_for
import os
import fitz 
import openai
import json


app = Flask(__name__)

#Add OpenAi's Api Key Here
api_key = 'sk-'
openai.api_key = api_key

def req_gpt(AnswerSheet, StudentPaper):
    def generate_response(prompt):
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=500,
            temperature=0
        )
        return response['choices'][0]['text']
    Marks = ''
    user_prompt = (
        f'''Assume you are an exam checker. Use the answer sheet for the correct answers.
        Check the student's paper and return student id(if its included in the paper, otherwise use 'null'), 
        marks accquired in each question's answer.
        total marks, total acquired marks, reasoning for the marking i.e what were the mistakes 
        and a 2 line feedback for the student so they can improve.
        Evaluate answers based on context and understanding, not just grammar or phrasing.
        Answer sheet: {AnswerSheet}. Student paper: {StudentPaper}.
        provide answer in this json format:
        {{
        "student_id": "",
        "marks": {{
        "question_1": "marks accquired in question_1",
        "question_2": "marks accquired in question_2",
        "question_n": "marks accquired in question_n"
        }},
        "total_marks": "",
        "total_marks_accquired": "",
        "reasoning": {{
        "question_1": "reason",
        "question_2": "reason",
        "question_n": "reason"
        }},
        "feedback": ""
    }}'''
    )
    output_response = generate_response(user_prompt)
    return(output_response)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as pdf_document:
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text += page.get_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return text

@app.route('/grading', methods=['GET', 'POST'])
def grading():
    if request.method == 'POST':
        if 'answerSheet' in request.files and 'studentCopies' in request.files:
            answer_sheet = request.files['answerSheet']
            student_copies = request.files.getlist('studentCopies')

            answer_sheet_path = os.path.join(app.config['UPLOAD_FOLDER'], answer_sheet.filename)
            answer_sheet.save(answer_sheet_path)

            student_texts = []

            for i, student_copy in enumerate(student_copies):
                student_copy_path = os.path.join(app.config['UPLOAD_FOLDER'], f'student_copy_{i + 1}.pdf')
                student_copy.save(student_copy_path)

                student_copy_text = extract_text_from_pdf(student_copy_path)
                student_texts.append(student_copy_text)

            answer_sheet_text = extract_text_from_pdf(answer_sheet_path)

            return redirect(url_for('results', answer_sheet_text=answer_sheet_text, student_texts=student_texts))
        else:
            return "Files not found in the request."

    return render_template('grading.html')

@app.route('/results')
def results():
    referrer = request.referrer
    if referrer and "grading" in referrer:
        answer_sheet_text = request.args.get('answer_sheet_text', '')
        student_texts = request.args.getlist('student_texts')

        results_list = []

        for i, student_copy_text in enumerate(student_texts):
            result = req_gpt(answer_sheet_text, student_copy_text)
            result_dict = json.loads(result)
            results_list.append(result_dict)
        print(results_list)
        return render_template('results.html', results_list=results_list)
    else:
        return redirect(url_for('home'))


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/howto')
def howto():
    return render_template('howto.html')

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)