import os
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from pdf2docx import Converter
from docx2pdf import convert as docx_to_pdf
from PIL import Image
from deep_translator import GoogleTranslator
from docx import Document
import PyPDF2
import magic
import uuid

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['SITE_NAME'] = 'Convert My File'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'png', 'jpg', 'jpeg', 'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html', site_name=app.config['SITE_NAME'])

# --- CONVERTER ROUTES ---

@app.route('/converter')
def converter_page():
    return render_template('converter.html', site_name=app.config['SITE_NAME'])

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        base_name, extension = os.path.splitext(filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(input_path)
        
        output_filename = ""
        output_path = ""
        
        try:
            if extension.lower() == '.pdf':
                # PDF to DOCX
                output_filename = f"{base_name}.docx"
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{output_filename}")
                cv = Converter(input_path)
                cv.convert(output_path, start=0, end=None)
                cv.close()
            
            elif extension.lower() == '.docx':
                # DOCX to PDF
                output_filename = f"{base_name}.pdf"
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{output_filename}")
                docx_to_pdf(input_path, output_path)
            
            elif extension.lower() in ['.png', '.jpg', '.jpeg']:
                # Image to PDF
                output_filename = f"{base_name}.pdf"
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{output_filename}")
                image = Image.open(input_path)
                image_rgb = image.convert('RGB')
                image_rgb.save(output_path)
            
            return send_file(output_path, as_attachment=True, download_name=output_filename)
            
        except Exception as e:
            flash(f"Error during conversion: {str(e)}")
            return redirect(url_for('converter_page'))
            
    return redirect(url_for('converter_page'))

# --- TRANSLATOR ROUTES ---

@app.route('/translator')
def translator_page():
    languages = {
        'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German', 
        'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'zh-CN': 'Chinese (Simplified)', 
        'ja': 'Japanese', 'ko': 'Korean', 'ar': 'Arabic', 'hi': 'Hindi', 
        'bn': 'Bengali', 'pa': 'Punjabi', 'jv': 'Javanese', 'ms': 'Malay', 
        'vi': 'Vietnamese', 'te': 'Telugu', 'mr': 'Marathi', 'ta': 'Tamil', 
        'tr': 'Turkish', 'ur': 'Urdu', 'gu': 'Gujarati', 'pl': 'Polish', 
        'uk': 'Ukrainian', 'ml': 'Malayalam', 'kn': 'Kannada', 'or': 'Odia', 
        'as': 'Assamese', 'bh': 'Bhojpuri'
    }
    return render_template('translator.html', site_name=app.config['SITE_NAME'], languages=languages)

@app.route('/translate', methods=['POST'])
def translate_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    target_lang = request.form.get('target_lang', 'en')
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        base_name, extension = os.path.splitext(filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(input_path)
        
        output_filename = f"{base_name}_{target_lang}{extension}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{output_filename}")
        
        try:
            translator = GoogleTranslator(source='auto', target=target_lang)
            
            if extension.lower() == '.docx':
                doc = Document(input_path)
                for para in doc.paragraphs:
                    if para.text.strip():
                        para.text = translator.translate(para.text)
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            if cell.text.strip():
                                cell.text = translator.translate(cell.text)
                doc.save(output_path)
            
            elif extension.lower() == '.pdf':
                reader = PyPDF2.PdfReader(input_path)
                full_text = ""
                for page in reader.pages:
                    full_text += page.extract_text() + "\n"
                
                translated_text = ""
                max_chars = 4500
                chunks = [full_text[i:i+max_chars] for i in range(0, len(full_text), max_chars)]
                for chunk in chunks:
                    if chunk.strip():
                        translated_text += translator.translate(chunk) + "\n"
                
                output_filename = f"{base_name}_{target_lang}.txt"
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{output_filename}")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(translated_text)
            
            elif extension.lower() == '.txt':
                with open(input_path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                translated_text = ""
                max_chars = 4500
                chunks = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
                for chunk in chunks:
                    if chunk.strip():
                        translated_text += translator.translate(chunk) + "\n"
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(translated_text)
            
            return send_file(output_path, as_attachment=True, download_name=output_filename)
            
        except Exception as e:
            flash(f"Error during translation: {str(e)}")
            return redirect(url_for('translator_page'))
            
    return redirect(url_for('translator_page'))

# --- MERGER ROUTES ---

@app.route('/merger')
def merger_page():
    return render_template('merger.html', site_name=app.config['SITE_NAME'])

@app.route('/merge', methods=['POST'])
def merge_files():
    if 'files' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        flash('No selected files')
        return redirect(request.url)
    
    merger = PyPDF2.PdfWriter()
    unique_id = str(uuid.uuid4())
    temp_files = []
    
    try:
        for file in files:
            if file and file.filename.lower().endswith('.pdf'):
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
                file.save(path)
                temp_files.append(path)
                merger.append(path)
            else:
                flash(f"Skipping non-PDF file: {file.filename}")
        
        output_filename = "merged_documents.pdf"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{output_filename}")
        merger.write(output_path)
        merger.close()
        
        return send_file(output_path, as_attachment=True, download_name=output_filename)
        
    except Exception as e:
        flash(f"Error during merging: {str(e)}")
        return redirect(url_for('merger_page'))
    finally:
        # Cleanup temp files could be added here
        pass

# --- COMPRESSOR ROUTES ---

@app.route('/compressor')
def compressor_page():
    return render_template('compressor.html', site_name=app.config['SITE_NAME'])

@app.route('/compress', methods=['POST'])
def compress_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    compression_level = request.form.get('level', 'medium')
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        base_name, extension = os.path.splitext(filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(input_path)
        
        output_filename = f"compressed_{filename}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{output_filename}")
        
        try:
            if extension.lower() == '.pdf':
                reader = PyPDF2.PdfReader(input_path)
                writer = PyPDF2.PdfWriter()
                
                for page in reader.pages:
                    # Compress content stream
                    page.compress_content_streams()
                    writer.add_page(page)
                
                # Quality levels for PDF are limited in PyPDF2; 
                # mainly content stream compression and metadata removal
                with open(output_path, "wb") as f:
                    writer.write(f)
            
            elif extension.lower() in ['.png', '.jpg', '.jpeg']:
                img = Image.open(input_path)
                
                # Setup quality based on level
                quality = 85 # Medium
                if compression_level == 'low':
                    quality = 95
                elif compression_level == 'high':
                    quality = 60
                
                # PNG doesn't support 'quality' in save the same way, usually use optimize and compress_level
                if extension.lower() == '.png':
                    img.save(output_path, optimize=True)
                else:
                    img.save(output_path, quality=quality, optimize=True)
            
            else:
                flash("Unsupported file type for compression")
                return redirect(url_for('compressor_page'))
            
            return send_file(output_path, as_attachment=True, download_name=output_filename)
            
        except Exception as e:
            flash(f"Error during compression: {str(e)}")
            return redirect(url_for('compressor_page'))
            
    return redirect(url_for('compressor_page'))

if __name__ == '__main__':
    app.run(debug=True)
