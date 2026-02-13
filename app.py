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
    ext = os.path.splitext(filename)[1].lower().replace('.', '')
    
    from converter import FILE_CONVERSIONS
    
    if ext in FILE_CONVERSIONS and target_format in FILE_CONVERSIONS[ext]:
        conversion_func = FILE_CONVERSIONS[ext][target_format]
        success, message = conversion_func(input_path, output_path)
    else:
        return jsonify({'success': False, 'error': f'Unsupported conversion: {ext} to {target_format}'}), 400
    
    if success:
        return jsonify({
            'success': True,
            'message': message,
            'download_url': f'/download/{output_filename}'
        })
    else:
        return jsonify({'success': False, 'error': message}), 500

@app.route('/convert-image', methods=['POST'])
def convert_image_route():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No image uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No image selected'}), 400
    
    target_format = request.form.get('format', 'jpg')
    quality = int(request.form.get('quality', 90))
    
    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
    file.save(input_path)
    
    base_name = os.path.splitext(filename)[0]
    output_filename = f"converted_{unique_id}_{base_name}.{target_format}"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    
    from converter import convert_image_to_image, convert_image_to_pdf
    
    success = False
    message = ""
    
    if target_format == 'pdf':
        success, message = convert_image_to_pdf(input_path, output_path)
    else:
        success, message = convert_image_to_image(input_path, output_path, target_format, quality)
        
    if success:
        return jsonify({
            'success': True,
            'message': message,
            'download_url': f'/download/{output_filename}'
        })
    else:
        return jsonify({'success': False, 'error': message}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
