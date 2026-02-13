import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory, flash, redirect, url_for
from werkzeug.utils import secure_filename
from converter_universal import convert_pdf_to_docx, convert_image_to_pdf, convert_docx_to_pdf, convert_image_to_image
from translator_engine import LANGUAGES, translate_file

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
    return render_template('translator.html', site_name=app.config['SITE_NAME'], languages=LANGUAGES)

@app.route('/merger')
def merger():
    return render_template('merger.html', site_name=app.config['SITE_NAME'])

@app.route('/merge', methods=['POST'])
def merge_pdfs():
    """Handle PDF merging"""
    if 'files' not in request.files:
        flash('No files uploaded')
        return redirect(url_for('merger'))
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        flash('No files selected')
        return redirect(url_for('merger'))
    
    from PyPDF2 import PdfMerger
    merger = PdfMerger()
    
    unique_id = str(uuid.uuid4())
    temp_files = []
    
    try:
        for file in files:
            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"tmp_{unique_id}_{filename}")
            file.save(temp_path)
            temp_files.append(temp_path)
            merger.append(temp_path)
        
        output_filename = f"merged_{unique_id}.pdf"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        with open(output_path, 'wb') as f:
            merger.write(f)
        
        merger.close()
        
        # Cleanup temp files
        for tmp in temp_files:
            try:
                os.remove(tmp)
            except:
                pass
                
        return send_from_directory(app.config['UPLOAD_FOLDER'], output_filename, as_attachment=True)
    
    except Exception as e:
        flash(f'Merging failed: {str(e)}')
        return redirect(url_for('merger'))

@app.route('/compressor')
def compressor():
    return render_template('compressor.html', site_name=app.config['SITE_NAME'])

@app.route('/compress', methods=['POST'])
def compress():
    """Handle file compression (PDF and Images)"""
    if 'file' not in request.files:
        flash('No file uploaded')
        return redirect(url_for('compressor'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('compressor'))
    
    quality = int(request.form.get('quality', 60))
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
    file.save(input_path)
    
    # Get extension
    ext = os.path.splitext(filename)[1].lower().replace('.', '')
    
    output_filename = f"compressed_{unique_id}_{filename}"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    
    try:
        if ext == 'pdf':
            from PyPDF2 import PdfReader, PdfWriter
            reader = PdfReader(input_path)
            writer = PdfWriter()
            
            for page in reader.pages:
                page.compress_content_streams() # Basic compression
                writer.add_page(page)
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            success, message = True, "PDF compressed"
        
        elif ext in ['jpg', 'jpeg', 'png', 'webp']:
            from PIL import Image
            img = Image.open(input_path)
            if img.mode != 'RGB' and ext in ['jpg', 'jpeg']:
                img = img.convert('RGB')
            
            img.save(output_path, quality=quality, optimize=True)
            success, message = True, "Image compressed"
        else:
            success, message = False, f"Format {ext} not supported for compression"
            
        if success and os.path.exists(output_path):
            return send_from_directory(app.config['UPLOAD_FOLDER'], output_filename, as_attachment=True)
        else:
            flash(f'Compression failed: {message}')
            return redirect(url_for('compressor'))
            
    except Exception as e:
        flash(f'Compression failed: {str(e)}')
        return redirect(url_for('compressor'))

@app.route('/convert', methods=['POST'])
def convert_file_universal():
    """Universal file converter - handles all formats"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    target_format = request.form.get('format', '').lower()
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
    file.save(input_path)
    
    # Get file extension
    source_format = os.path.splitext(filename)[1].lower().replace('.', '')
    
    # Generate output filename
    base_name = os.path.splitext(filename)[0]
    output_filename = f"converted_{unique_id}_{base_name}.{target_format}"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    
    # Import converter
    from converter_universal import convert_file
    
    # Perform conversion
    success, message = convert_file(input_path, output_path, source_format, target_format)
    
    if success and os.path.exists(output_path):
        return jsonify({
            'success': True,
            'message': message,
            'download_url': f'/download/{output_filename}',
            'filename': output_filename
        })
    else:
        return jsonify({'success': False, 'error': message}), 500

@app.route('/convert-image', methods=['POST'])
def convert_image():
    """Handle image conversions (JPG, PNG, WebP, PDF)"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    target_format = request.form.get('format', 'jpg')
    quality = int(request.form.get('quality', 90))
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
    file.save(input_path)
    
    # Generate output filename
    base_name = os.path.splitext(filename)[0]
    output_filename = f"converted_{unique_id}_{base_name}.{target_format}"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    
    # Handle conversion
    if target_format == 'pdf':
        success, message = convert_image_to_pdf(input_path, output_path)
    else:
        success, message = convert_image_to_image(input_path, output_path, target_format, quality)
    
    if success and os.path.exists(output_path):
        return jsonify({
            'success': True,
            'message': message,
            'download_url': f'/download/{output_filename}',
            'filename': output_filename
        })
    else:
        return jsonify({'success': False, 'error': message}), 500

@app.route('/translate', methods=['POST'])
def translate():
    """Handle document translation"""
    if 'file' not in request.files:
        flash('No file uploaded')
        return redirect(url_for('translator'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('translator'))
    
    target_lang = request.form.get('target_lang', 'en')
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
    file.save(input_path)
    
    # Get extension
    ext = os.path.splitext(filename)[1].lower().replace('.', '')
    
    # Generate output name
    # For PDF, we translate to TXT for simplicity in this version
    target_ext = 'txt' if ext == 'pdf' else ext
    output_filename = f"translated_{unique_id}_{os.path.splitext(filename)[0]}.{target_ext}"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    
    # Translate
    success, message = translate_file(input_path, output_path, ext, target_lang)
    
    if success and os.path.exists(output_path):
        return jsonify({
            'success': True,
            'message': message,
            'download_url': f'/download/{output_filename}',
            'preview_filename': output_filename,
            'filename': output_filename
        })
    else:
        return jsonify({'success': False, 'error': message}), 500

@app.route('/get-preview/<filename>')
def get_preview(filename):
    """Retrieve text content for previewing"""
    filename = secure_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'File not found'}), 404
        
    ext = os.path.splitext(filename)[1].lower().replace('.', '')
    
    try:
        if ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(10000) # Preview first 10k chars
            return jsonify({'success': True, 'content': content, 'type': 'text'})
            
        elif ext == 'docx':
            from docx import Document
            doc = Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            content = "\n".join(full_text)[:10000]
            return jsonify({'success': True, 'content': content, 'type': 'text'})
            
        elif ext == 'pdf':
            # Note: Translated PDFs in this app are currently saved as .txt
            # If it's a real PDF, we'd need extraction, but existing engine saves it as txt
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(10000)
            return jsonify({'success': True, 'content': content, 'type': 'text'})
            
        return jsonify({'success': False, 'error': f'Preview not available for {ext} format'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
