import os
import re
import time
import PyPDF2
from deep_translator import GoogleTranslator
from docx import Document
import openpyxl
import csv

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
    """Check if text should be kept as-is (not translated)"""
    if not isinstance(text, str):
        return True
    text = text.strip()
    if not text or len(text) < 2:
        return True
    for pattern in PRESERVE_PATTERNS:
        if re.match(pattern, text):
            return True
    # Check if mostly numbers
    letters = sum(c.isalpha() for c in text)
    numbers = sum(c.isdigit() for c in text)
    if numbers > letters and numbers > 3:
        return True
    return False

# ===== FIXED TRANSLATE FUNCTION WITH CHUNKING AND RETRY =====
def translate_text(text, target_lang, source_lang='auto', max_retries=3):
    """Safe translation with chunking and retry logic"""
    if should_preserve(text):
        return text
    
    # Split long text into smaller chunks (Google limit ~5000 chars)
    chunk_size = 4000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    translated_chunks = []
    
    for chunk in chunks:
        for attempt in range(max_retries):
            try:
                translator = GoogleTranslator(source=source_lang, target=target_lang[:2])
                result = translator.translate(chunk)
                if result:
                    translated_chunks.append(result)
                    break
                time.sleep(1)
            except Exception as e:
                print(f"Translation attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    translated_chunks.append(chunk)  # Fallback to original
                time.sleep(2)
    
    return ' '.join(translated_chunks)

# ===== PDF TRANSLATOR =====
def translate_pdf(input_path, output_path, target_lang, source_lang='auto'):
    """Translate PDF while preserving structure"""
    try:
        text_content = []
        with open(input_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            for i, page in enumerate(pdf_reader.pages):
                print(f"Translating page {i+1}/{total_pages}")
                text = page.extract_text()
                if text and text.strip():
                    translated = translate_text(text, target_lang, source_lang)
                    text_content.append(translated)
                else:
                    text_content.append("")
        
        output_txt = output_path.replace('.pdf', '.txt')
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(text_content))
        
        return True, f"PDF translation completed: {total_pages} pages"
    except Exception as e:
        print(f"PDF translation error: {e}")
        return False, str(e)

# ===== WORD DOCUMENT TRANSLATOR =====
def translate_docx(input_path, output_path, target_lang, source_lang='auto'):
    """Translate Word document preserving tables and formatting"""
    try:
        doc = Document(input_path)
        for para in doc.paragraphs:
            if para.text and not should_preserve(para.text):
                para.text = translate_text(para.text, target_lang, source_lang)
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if para.text and not should_preserve(para.text):
                            para.text = translate_text(para.text, target_lang, source_lang)
        
        doc.save(output_path)
        return True, "Word translation completed"
    except Exception as e:
        return False, str(e)

# ===== EXCEL TRANSLATOR =====
def translate_excel(input_path, output_path, target_lang, source_lang='auto'):
    """Translate Excel files preserving all sheets and structure"""
    try:
        wb = openpyxl.load_workbook(input_path)
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value and isinstance(cell.value, str):
                        if not should_preserve(cell.value):
                            cell.value = translate_text(cell.value, target_lang, source_lang)
        
        wb.save(output_path)
        return True, "Excel translation completed"
    except Exception as e:
        return False, str(e)

# ===== CSV TRANSLATOR =====
def translate_csv(input_path, output_path, target_lang, source_lang='auto'):
    """Translate CSV files"""
    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            rows = []
            for row in reader:
                new_row = []
                for cell in row:
                    if should_preserve(cell):
                        new_row.append(cell)
                    else:
                        new_row.append(translate_text(cell, target_lang, source_lang))
                rows.append(new_row)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerows(rows)
        return True, "CSV translation completed"
    except Exception as e:
        return False, str(e)

# ===== TEXT FILE TRANSLATOR =====
def translate_text_file(input_path, output_path, target_lang, source_lang='auto'):
    """Translate plain text files"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        translated = translate_text(content, target_lang, source_lang)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated)
        return True, "Text translation completed"
    except Exception as e:
        return False, str(e)

# ===== MAIN DISPATCHER FUNCTION =====
def translate_document(input_path, output_path, target_lang, source_lang='auto', file_ext=None):
    """Main dispatcher function - THIS IS WHAT app.py CALLS"""
    if file_ext is None:
        file_ext = os.path.splitext(input_path)[1].lower()
    
    translators = {
        '.pdf': translate_pdf,
        '.docx': translate_docx,
        '.doc': translate_docx,
        '.xlsx': translate_excel,
        '.xls': translate_excel,
        '.csv': translate_csv,
        '.txt': translate_text_file,
    }
    
    translator = translators.get(file_ext)
    if translator:
        return translator(input_path, output_path, target_lang, source_lang)
    else:
        return False, f"Unsupported file type: {file_ext}"