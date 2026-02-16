# Standard library imports
import os
import uuid

# Flask related imports
from flask import Flask, render_template, request, jsonify, send_from_directory, flash, redirect, url_for
from werkzeug.utils import secure_filename

# Note: heavy imports (translator_engine, converter_universal, etc.) 
# are moved inside routes or after app initialization.

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
    from translator_engine import LANGUAGES
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
    """Handle file compression with target size (PDF and Images)"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    try:
        target_val = float(request.form.get('target_size', 0))
        unit = request.form.get('unit', 'KB').upper()
        
        # Target size in bytes
        target_bytes = target_val * 1024 if unit == 'KB' else target_val * 1024 * 1024
        
        # Enforcement: 5KB to 50MB
        min_bytes = 5 * 1024
        max_bytes = 50 * 1024 * 1024
        
        if target_bytes < min_bytes or target_bytes > max_bytes:
            return jsonify({'success': False, 'error': 'We can process 5KB-50MB files'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(input_path)
        
        # Get extension
        ext = os.path.splitext(filename)[1].lower().replace('.', '')
        output_filename = f"processed_{unique_id}_{filename}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        success = False
        message = ""

        if ext in ['jpg', 'jpeg', 'png', 'webp']:
            from PIL import Image
            import io
            
            orig_img = Image.open(input_path)
            orig_format = 'JPEG' if ext in ['jpg', 'jpeg'] else ext.upper()
            
            # --- Lever 1: Quality Tuning ---
            low_q, high_q = 1, 100
            best_q = 75
            
            for _ in range(7):
                mid_q = (low_q + high_q) // 2
                buf = io.BytesIO()
                
                # Parameters for format
                params = {'format': orig_format, 'optimize': True}
                if orig_format in ['JPEG', 'WEBP']: params['quality'] = mid_q
                elif orig_format == 'PNG': params['compress_level'] = mid_q // 11
                
                temp_img = orig_img
                if temp_img.mode != 'RGB' and orig_format == 'JPEG':
                    temp_img = temp_img.convert('RGB')
                    
                temp_img.save(buf, **params)
                if buf.tell() <= target_bytes:
                    best_q = mid_q
                    low_q = mid_q + 1
                else:
                    high_q = mid_q - 1

            # Check if Lever 1 was enough
            final_buf = io.BytesIO()
            test_params = {'format': orig_format, 'optimize': True}
            if orig_format in ['JPEG', 'WEBP']: test_params['quality'] = best_q
            elif orig_format == 'PNG': test_params['compress_level'] = best_q // 11
            
            temp_img = orig_img
            if temp_img.mode != 'RGB' and orig_format == 'JPEG':
                temp_img = temp_img.convert('RGB')
            temp_img.save(final_buf, **test_params)
            
            current_size = final_buf.tell()
            
            # --- Lever 2: Precision Convergence Loop (v3.0) ---
            # We iteratively recalibrate dimensions based on actual size feedback
            current_scale = 1.0
            tolerance = 0.05 # 5% error margin
            working_img = orig_img
            
            for attempt in range(5):
                # Calculate dimensions for this pass
                temp_w = max(1, int(orig_img.width * current_scale))
                temp_h = max(1, int(orig_img.height * current_scale))
                
                # Resize from ORIGINAL to avoid compound blur
                working_img = orig_img.resize((temp_w, temp_h), Image.Resampling.LANCZOS)
                if working_img.mode != 'RGB' and orig_format == 'JPEG':
                    working_img = working_img.convert('RGB')
                
                # Check output size
                buf = io.BytesIO()
                working_img.save(buf, **test_params)
                current_size = buf.tell()
                
                # Are we close enough?
                if abs(current_size - target_bytes) / target_bytes <= tolerance:
                    break
                
                # Recalculate scale based on actual size result
                # Ratio is sqrt(Target/Actual) because size is area-proportional
                scale_adjustment = (target_bytes / current_size) ** 0.5
                current_scale *= scale_adjustment
                
                # Safety boundaries (0.1x to 4.0x original)
                current_scale = max(0.05, min(8.0, current_scale))

            # Final Save
            working_img.save(output_path, **test_params)
            success, message = True, f"Precision calibrated ({unit}) after {attempt+1} passes"
            
        elif ext == 'pdf':
            # PDF compression is less granular with PyPDF2
            from PyPDF2 import PdfReader, PdfWriter
            reader = PdfReader(input_path)
            writer = PdfWriter()
            for page in reader.pages:
                page.compress_content_streams()
                writer.add_page(page)
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            success, message = True, "PDF processed with standard compression"
        else:
            success, message = False, f"Format {ext} not supported for target-size processing"

        if success and os.path.exists(output_path):
            return jsonify({
                'success': True,
                'message': message,
                'download_url': f'/download/{output_filename}',
                'filename': output_filename
            })
        else:
            return jsonify({'success': False, 'error': message or "Processing failed"}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
    from converter_universal import convert_image_to_pdf, convert_image_to_image
    
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
def translate_file_route():
    """Translate uploaded documents with robust error handling"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        target_lang = request.form.get('target_lang', 'es')
        source_lang = request.form.get('source_lang', 'auto')
        
        # Validate file size (50MB max)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 50 * 1024 * 1024:
            return jsonify({'success': False, 'error': 'File too large (max 50MB)'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(input_path)
        
        # Generate output path
        file_ext = os.path.splitext(filename)[1].lower()
        base_name = os.path.splitext(filename)[0]
        output_filename = f"translated_{unique_id}_{base_name}{file_ext}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # Import translator function
        from translator_engine import translate_document
        
        # Handle PDF to TXT conversion path early
        if file_ext == '.pdf':
            output_path = output_path.replace('.pdf', '.txt')
            
        # Translate with timeout
        success, message = translate_document(
            input_path, output_path, target_lang, source_lang, file_ext
        )
        
        # Update output_filename for response
        output_filename = os.path.basename(output_path)
        
        if success and os.path.exists(output_path):
            # Verify the translation is valid for the target language
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    translated_sample = f.read(1000)
                
                with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # Note: For non-text files, this might be garbled, but that's okay for similarity check
                    original_sample = f.read(1000) 
                
                from translator_engine import is_valid_translation
                if not is_valid_translation(translated_sample, target_lang, original_sample):
                    try:
                        print(f"WARNING: Translation to {target_lang} may be invalid or same as original")
                    except UnicodeEncodeError:
                        pass
            except Exception as ve:
                try:
                    print(f"Validation warning: {ve}")
                except UnicodeEncodeError:
                    pass
            
            return jsonify({
                'success': True,
                'message': message,
                'download_url': f'/download/{output_filename}',
                'filename': output_filename,
                'preview_filename': output_filename
            })
        else:
            return jsonify({'success': False, 'error': message or 'Translation failed'}), 500
            
    except Exception as e:
        try:
            print(f"Translation route error: {e}")
            import traceback
            traceback.print_exc()
        except UnicodeEncodeError:
            pass
        return jsonify({'success': False, 'error': str(e)}), 500

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
            # Use PyPDF2 to extract text from the translated PDF for preview
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                content = ""
                # Get text from first few pages to show in preview
                for page_idx in range(min(len(reader.pages), 5)):
                    content += reader.pages[page_idx].extract_text() + "\n"
            return jsonify({'success': True, 'content': content[:10000], 'type': 'text'})
            
        return jsonify({'success': False, 'error': f'Preview not available for {ext} format'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
