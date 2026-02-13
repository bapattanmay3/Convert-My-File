import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from converter import convert_pdf_to_docx, convert_image_to_pdf, convert_docx_to_pdf

app = Flask(__name__)
app.config['SITE_NAME'] = 'Convert My File'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html', site_name=app.config['SITE_NAME'])

@app.route('/converter')
def converter():
    return render_template('converter.html', site_name=app.config['SITE_NAME'])

@app.route('/translator')
def translator():
    # Placeholder for future implementation
    return render_template('translator.html', site_name=app.config['SITE_NAME'])

@app.route('/merger')
def merger():
    # Placeholder for future implementation
    return render_template('merger.html', site_name=app.config['SITE_NAME'])

@app.route('/compressor')
def compressor():
    # Placeholder for future implementation
    return render_template('compressor.html', site_name=app.config['SITE_NAME'])

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    target_format = request.form.get('format', 'docx')
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
    file.save(input_path)
    
    # Generate output filename
    base_name = os.path.splitext(filename)[0]
    output_filename = f"converted_{unique_id}_{base_name}.{target_format}"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    
    # Convert based on file type and target format
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == '.pdf' and target_format == 'docx':
        success, message = convert_pdf_to_docx(input_path, output_path)
    elif ext in ['.jpg', '.jpeg', '.png'] and target_format == 'pdf':
        success, message = convert_image_to_pdf(input_path, output_path)
    elif ext == '.docx' and target_format == 'pdf':
        success, message = convert_docx_to_pdf(input_path, output_path)
    else:
        return jsonify({'success': False, 'error': 'Unsupported conversion'}), 400
    
    if success:
        return jsonify({
            'success': True,
            'download_url': f'/download/{output_filename}'
        })
    else:
        return jsonify({'success': False, 'error': message}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
