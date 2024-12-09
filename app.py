from flask import Flask, render_template, request, send_file, jsonify, logging 
import sqlite3
import os
import glob

app = Flask(__name__)
app.config['DATA_DATABASE'] = 'database/data.db'
app.config['QUIZ_DATABASE'] = 'database/quiz.db'
app.config['UPLOAD_FOLDER'] = 'static/pdfs'

# Connect to the data.db database
def get_data_db():
    conn = sqlite3.connect(app.config['DATA_DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Connect to the quiz.db database
def get_quiz_db():
    conn = sqlite3.connect(app.config['QUIZ_DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Functions related to data.db

def get_categories():
    conn = get_data_db()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT Subject.id, Subject.name FROM Criteria JOIN Subject ON Criteria.subject_id = Subject.id')
    categories = cursor.fetchall()
    conn.close()
    return categories

@app.route('/')
def index():
    years = [2566, 2565, 2564, 2563, 2562, 2561, 2560, 2559, 2558, 2557, 2556, 2555, 2554]
    categories = get_categories()
    return render_template('index.html', years=years, categories=categories, data={})

@app.route('/select', methods=['POST'])
def select_pdf():
    year = request.form['year']
    subject = request.form['subject']
    conn = get_data_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Criteria WHERE Criteria.years_id = ? AND Criteria.subject_id = ?', (year, subject))
    pdfs = cursor.fetchall()
    return render_template('index.html', pdfs=pdfs)

@app.route('/select_file', methods=['POST'])
def select_file():
    category = request.form['category']
    subcategory = request.form['subcategory']
    year = request.form['year']

    if year == 'all':
        # Retrieve all PDFs for the given category and subcategory
        file_pattern = f"{category}_{subcategory}_*.pdf"  # Pattern to match all files for the given category and subcategory
        file_paths = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], file_pattern))
        if file_paths:
            # If there are files matching the pattern
            app.logger.info(f"Found {len(file_paths)} files for category {category}, subcategory {subcategory}, and year 'all'.")
            return jsonify({'file_paths': file_paths})
        else:
            # If no files are found
            app.logger.warning(f"No files found for category {category}, subcategory {subcategory}, and year 'all'.")
            return jsonify({'error': 'No files found for the selected criteria.'}), 404

    else:
        # Otherwise, retrieve PDFs based on specific criteria
        conn = get_data_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Criteria WHERE subcategory_id = ? AND years_id = ?', (subcategory, year))
        pdfs = cursor.fetchall()
        conn.close()
        return render_template('index.html', pdfs=pdfs)

@app.route('/view_pdf/<file_path_id>', methods=['GET'])
def view_pdf(file_path_id):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_path_id)
    app.logger.info(f"Constructed file path: {file_path}")
    return send_file(file_path, as_attachment=False)

@app.route('/get_file_path_id', methods=['POST'])
def get_file_path_id():
    data = request.get_json()
    category = data.get('category')
    year = data.get('year')
    subcategory = data.get('subcategory')

    if year == 'all':
        file_pattern = f"{category}_{subcategory}_*.pdf"
        file_paths = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], file_pattern))
        if file_paths:
            app.logger.info(f"Found {len(file_paths)} files for category {category}, subcategory {subcategory}, and year 'all'.")
            return jsonify({'file_paths': file_paths})
        else:
            app.logger.warning(f"No files found for category {category}, subcategory {subcategory}, and year 'all'.")
            return jsonify({'error': 'No files found for the selected criteria.'}), 404
    else:
        # Construct file path based on specific criteria
        file_path_id = f"{category}_{subcategory}_{year}.pdf"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_path_id)
        if os.path.exists(file_path):
            app.logger.info(f"File path found for specific criteria: {file_path}")
            return jsonify({'file_path_id': file_path_id})
        else:
            app.logger.error(f"File path not found for specific criteria: {file_path}")
            return jsonify({'file_path_id': None, 'error': 'File path not found for the selected criteria.'}), 404



@app.route('/index2')
def index2():
    return render_template('index2.html')

# Functions related to quiz.db

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/store_summary_score', methods=['POST'])
def store_summary_score():
    data = request.get_json()
    summary_score = data.get('summary_score')
    store_score_in_quiz_db(summary_score)
    return jsonify({'message': 'Summary score stored successfully.'})

@app.route('/user_percentile', methods=['GET'])
def get_user_percentile():
    default_value = 0
    score = int(request.args.get('score_TGAT', default_value))
    percentile = calculate_percentile(score)
    return jsonify({'percentile': percentile})

# Helper functions for quiz.db

def store_score_in_quiz_db(score):
    conn = get_quiz_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO scores (score_TGAT) VALUES (?)', (score,))
    conn.commit()
    conn.close()

def calculate_percentile(score):
    conn = get_quiz_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) AS total FROM scores')
    total_scores = cursor.fetchone()['total']
    cursor.execute('SELECT COUNT(*) AS count FROM scores WHERE score_TGAT <= ?', (score,))
    lower_or_equal_scores = cursor.fetchone()['count']
    percentile = (lower_or_equal_scores / total_scores) * 100
    conn.close()
    return percentile

# <---------------------------------------------------------->

@app.route('/quiz2')
def quiz2():
    return render_template('quiz2.html')

@app.route('/store_summary_score2', methods=['POST'])
def store_summary_score2():
    data = request.get_json()
    summary_score2 = data.get('summary_score2' )
    store_score_in_quiz_db2(summary_score2)
    return jsonify({'message': 'Summary score stored successfully.'})

@app.route('/user_percentile2', methods=['GET'])
def get_user_percentile2():
    default_value = 0
    score = int(request.args.get('score_Math1', default_value))
    percentile = calculate_percentile2(score)
    return jsonify({'percentile': percentile})

# Helper functions for quiz.db

def store_score_in_quiz_db2(score):
    conn = get_quiz_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO scores2 (score_Math1) VALUES (?)', (score,))
    conn.commit()
    conn.close()

def calculate_percentile2(score):
    conn = get_quiz_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) AS total FROM scores2')
    total_scores2 = cursor.fetchone()['total']
    cursor.execute('SELECT COUNT(*) AS count FROM scores2 WHERE score_Math1 <= ?', (score,))
    lower_or_equal_scores2 = cursor.fetchone()['count']
    percentile = (lower_or_equal_scores2 / total_scores2) * 100
    conn.close()
    return percentile


if __name__ == '__main__':
    app.run(debug=True)