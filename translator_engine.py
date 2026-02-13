import os
import re
import time
import PyPDF2
import translators as ts
from docx import Document
import openpyxl
import csv
import logging

# Configure safe logging
logging.basicConfig(
    filename='translator.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def safe_log(msg):
    """Safely log messages without crashing the console on Windows"""
    try:
        logging.error(msg)
        print(msg)
    except:
        pass

# ===== ENTITY PRESERVATION PATTERNS =====
PRESERVE_PATTERNS = [
    r'^[\d\s\+\-\(\)]+$',                    # Pure numbers
    r'^\d+$',                                 # Integers
    r'^\d+\.\d+$',                           # Decimals
    r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$',    # Dates
    r'^[\w\.-]+@[\w\.-]+\.\w+$',             # Emails
    r'^https?://[^\s]+$',                    # URLs
    r'^[A-Z0-9]{5,}$',                       # Codes/IDs
    r'^[A-Z]{2,}\d+$',                       # Alphanumeric codes
    r'^\$\s*\d+(\.\d{2})?$',                 # Prices
    r'^\d+(\.\d{1,2})?%$',                   # Percentages
]

def should_preserve(text):
    """Check if text should be excluded from translation"""
    if not isinstance(text, str):
        return True
    text = text.strip()
    if not text or len(text) < 2:
        return True
    for pattern in PRESERVE_PATTERNS:
        if re.match(pattern, text):
            return True
    letters = sum(c.isalpha() for c in text)
    numbers = sum(c.isdigit() for c in text)
    if numbers > letters and numbers > 3:
        return True
    return False

def translate_text_safe(text, target_lang, source_lang='auto', max_retries=3):
    """Safe translation using translators library (more stable)"""
    if not text or not text.strip():
        return text
    if should_preserve(text):
        return text
    
    # Map language codes
    lang_map = {
        'es': 'es', 'fr': 'fr', 'de': 'de', 'it': 'it', 'pt': 'pt',
        'ru': 'ru', 'zh': 'zh', 'ja': 'ja', 'ko': 'ko', 'ar': 'ar',
        'hi': 'hi', 'bn': 'bn', 'te': 'te', 'mr': 'mr', 'ta': 'ta',
        'gu': 'gu', 'kn': 'kn', 'ml': 'ml', 'pa': 'pa', 'ur': 'ur'
    }
    
    target = lang_map.get(target_lang[:2], target_lang[:2])
    
    # Chunk long text
    chunk_size = 4000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    translated_chunks = []
    
    for chunk in chunks:
        for attempt in range(max_retries):
            try:
                # Use google translate via translators library
                result = ts.google(chunk, from_language=source_lang, to_language=target)
                if result:
                    translated_chunks.append(result)
                    break
                time.sleep(1)
            except Exception as e:
                safe_log(f"Translation attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    translated_chunks.append(chunk)  # Fallback to original
                time.sleep(2)
    
    return ' '.join(translated_chunks)

def translate_pdf(input_path, output_path, target_lang, source_lang='auto'):
    """PDF translation with chunking"""
    try:
        text_content = []
        with open(input_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            for i, page in enumerate(pdf_reader.pages):
                safe_log(f"Translating page {i+1}/{total_pages}")
                text = page.extract_text()
                if text and text.strip():
                    translated = translate_text_safe(text, target_lang, source_lang)
                    text_content.append(translated)
                else:
                    text_content.append("")
        
        output_txt = output_path.replace('.pdf', '.txt')
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(text_content))
        
        return True, f"PDF translation completed: {total_pages} pages"
    except Exception as e:
        safe_log(f"PDF translation error: {e}")
        return False, str(e)

def translate_docx(input_path, output_path, target_lang):
    """DOCX Translation with deep table and formatting preservation"""
    try:
        doc = Document(input_path)
        for para in doc.paragraphs:
            if para.text.strip():
                para.text = translate_text_safe(para.text, target_lang)
                
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if para.text.strip():
                            para.text = translate_text_safe(para.text, target_lang)
                            
        doc.save(output_path)
        return True, "DOCX translated successfully"
    except Exception as e:
        return False, str(e)

def translate_xlsx(input_path, output_path, target_lang):
    """Excel to Translated Excel (Multi-sheet)"""
    try:
        import pandas as pd
        all_sheets = pd.read_excel(input_path, sheet_name=None)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in all_sheets.items():
                for col in df.columns:
                    df[col] = df[col].apply(lambda x: translate_text_safe(str(x), target_lang) if pd.notnull(x) and str(x).strip() else x)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
        return True, "Excel file translated successfully"
    except Exception as e:
        return False, str(e)

def translate_txt(input_path, output_path, target_lang):
    """TXT Translation"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
        translated_text = translate_text_safe(text, target_lang)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        return True, "Text file translated successfully"
    except Exception as e:
        return False, str(e)

def translate_csv(input_path, output_path, target_lang):
    """CSV Translation"""
    try:
        import pandas as pd
        df = pd.read_csv(input_path)
        for col in df.columns:
            df[col] = df[col].apply(lambda x: translate_text_safe(str(x), target_lang) if pd.notnull(x) and str(x).strip() else x)
        df.to_csv(output_path, index=False)
        return True, "CSV file translated successfully"
    except Exception as e:
        return False, str(e)

def translate_document(input_path, output_path, target_lang, source_lang='auto', file_ext=None):
    """Main dispatcher function using stable translators library"""
    try:
        if file_ext is None:
            file_ext = os.path.splitext(input_path)[1].lower()
        
        if not os.path.exists(input_path):
            return False, "Input file not found"
        
        if file_ext == '.pdf':
            return translate_pdf(input_path, output_path, target_lang, source_lang)
        elif file_ext == '.docx':
            return translate_docx(input_path, output_path, target_lang)
        elif file_ext in ['.xlsx', '.xls']:
            return translate_xlsx(input_path, output_path, target_lang)
        elif file_ext == '.csv':
            return translate_csv(input_path, output_path, target_lang)
        elif file_ext == '.txt':
            return translate_txt(input_path, output_path, target_lang)
        else:
            return False, f"Unsupported file type: {file_ext}"
            
    except Exception as e:
        safe_log(f"Critical translation error: {e}")
        return False, str(e)
