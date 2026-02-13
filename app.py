import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from converter import convert_pdf_to_docx, convert_image_to_pdf, convert_docx_to_pdf

app = Flask(__name__)
app.config['SITE_NAME'] = 'Convert My File'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html', site_name=app.config['SITE_NAME'])

@app.route('/converter')
def converter():
    return render_template('converter.html', site_name=app.config['SITE_NAME'])

@app.route('/translator')
def translator():
    return render_template('translator.html', site_name=app.config['SITE_NAME'])

@app.route('/merger')
def merger():
    return render_template('merger.html', site_name=app.config['SITE_NAME'])

@app.route('/compressor')
def compressor():
    return render_template('compressor.html', site_name=app.config['SITE_NAME'])

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    target_format = request.form.get('format')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
    
    if file:
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        input_filename = f"{unique_id}_{filename}"
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        file.save(input_path)
        
        output_filename = f"{unique_id}_converted.{target_format}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        success = False
        message = ""
        
        # Determine conversion type based on file extension and target format
        ext = filename.rsplit('.', 1)[1].lower()
        
        if ext == 'pdf' and target_format == 'docx':
            success, message = convert_pdf_to_docx(input_path, output_path)
        elif ext in ['jpg', 'jpeg', 'png'] and target_format == 'pdf':
            success, message = convert_image_to_pdf(input_path, output_path)
        elif ext == 'docx' and target_format == 'pdf':
            success, message = convert_docx_to_pdf(input_path, output_path)
        else:
            message = "Unsupported conversion"
        
        if success:
            return jsonify({
                'success': True,
                'download_url': f'/download/{output_filename}'
            })
        else:
            return jsonify({'success': False, 'error': message})

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
