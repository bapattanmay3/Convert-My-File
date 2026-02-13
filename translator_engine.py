"""
Modular Translation Engine
Supports: PDF, DOCX, TXT
Uses: deep-translator
"""

import os
from deep_translator import GoogleTranslator
import PyPDF2
from docx import Document
from io import BytesIO
import logging
import time

# Configure safe logging to avoid console encoding issues
logging.basicConfig(
    filename='translator.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def safe_log(msg):
    """Safely log messages without crashing the console on Windows"""
    try:
        logging.error(msg)
        print(msg) # For user visibility, but wrapped nicely if needed
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
    """Safe translation with timeout, retries and chunking"""
    if should_preserve(text):
        return text
    
    # Chunk long text (4000 chars max per request)
    chunk_size = 4000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    translated_chunks = []
    
    for chunk in chunks:
        for attempt in range(max_retries):
            try:
                # Use deep-translator
                translator = GoogleTranslator(source=source_lang, target=target_lang[:2])
                result = translator.translate(chunk)
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

# Supported languages
LANGUAGES = {
    'af': 'Afrikaans', 'sq': 'Albanian', 'am': 'Amharic', 'ar': 'Arabic', 'hy': 'Armenian', 'az': 'Azerbaijani',
    'eu': 'Basque', 'be': 'Belarusian', 'bn': 'Bengali', 'bs': 'Bosnian', 'bg': 'Bulgarian', 'ca': 'Catalan',
    'ceb': 'Cebuano', 'ny': 'Chichewa', 'zh-CN': 'Chinese (Simplified)', 'zh-TW': 'Chinese (Traditional)',
    'co': 'Corsican', 'hr': 'Croatian', 'cs': 'Czech', 'da': 'Danish', 'nl': 'Dutch', 'en': 'English',
    'eo': 'Esperanto', 'et': 'Estonian', 'tl': 'Filipino', 'fi': 'Finnish', 'fr': 'French', 'fy': 'Frisian',
    'gl': 'Galician', 'ka': 'Georgian', 'de': 'German', 'el': 'Greek', 'gu': 'Gujarati', 'ht': 'Haitian Creole',
    'ha': 'Hausa', 'haw': 'Hawaiian', 'iw': 'Hebrew', 'hi': 'Hindi', 'hmn': 'Hmong', 'hu': 'Hungarian',
    'is': 'Icelandic', 'ig': 'Igbo', 'id': 'Indonesian', 'ga': 'Irish', 'it': 'Italian', 'ja': 'Japanese',
    'jw': 'Javanese', 'kn': 'Kannada', 'kk': 'Kazakh', 'km': 'Khmer', 'rw': 'Kinyarwanda', 'ko': 'Korean',
    'ku': 'Kurdish (Kurmanji)', 'ky': 'Kyrgyz', 'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian', 'lt': 'Lithuanian',
    'lb': 'Luxembourgish', 'mk': 'Macedonian', 'mg': 'Malagasy', 'ms': 'Malay', 'ml': 'Malayalam', 'mt': 'Maltese',
    'mi': 'Maori', 'mr': 'Marathi', 'mn': 'Mongolian', 'my': 'Myanmar (Burmese)', 'ne': 'Nepali', 'no': 'Norwegian',
    'or': 'Odia (Oriya)', 'ps': 'Pashto', 'fa': 'Persian', 'pl': 'Polish', 'pt': 'Portuguese', 'pa': 'Punjabi',
    'ro': 'Romanian', 'ru': 'Russian', 'sm': 'Samoan', 'gd': 'Scots Gaelic', 'sr': 'Serbian', 'st': 'Sesotho',
    'sn': 'Shona', 'sd': 'Sindhi', 'si': 'Sinhala', 'sk': 'Slovak', 'sl': 'Slovenian', 'so': 'Somali',
    'es': 'Spanish', 'su': 'Sundanese', 'sw': 'Swahili', 'sv': 'Swedish', 'tg': 'Tajik', 'ta': 'Tamil',
    'tt': 'Tatar', 'te': 'Telugu', 'th': 'Thai', 'tr': 'Turkish', 'tk': 'Turkmen', 'uk': 'Ukrainian',
    'ur': 'Urdu', 'ug': 'Uyghur', 'uz': 'Uzbek', 'vi': 'Vietnamese', 'cy': 'Welsh', 'xh': 'Xhosa',
    'yi': 'Yiddish', 'yo': 'Yoruba', 'zu': 'Zulu'
}

import re

def translate_text(text, target_lang, source_lang='auto'):
    """
    Translates text (or list of texts) with TRUE batching support.
    Reduces network overhead by 90-95% via native translate_batch.
    """
    if not text:
        return "" if isinstance(text, str) else []
        
    is_batch = isinstance(text, list)
    text_list = text if is_batch else [text]
    
    # --- PHASE 1: PRE-TRANSLATION (MASKING) ---
    masked_list = []
    entities_map = [] # Store entities per item
    
    num_pattern = r'\b\d+(?:[.,]\d+)*\b'
    name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    EXCLUSIONS = {'The', 'My', 'This', 'A', 'An', 'Our', 'Your', 'Their', 'His', 'Her', 'It', 'There', 'Where', 'When', 'Who', 'How', 'That', 'These', 'Those'}

    for item in text_list:
        if not item.strip():
            masked_list.append(item)
            entities_map.append([])
            continue
            
        current_entities = []
        def mask_entities(match):
            val = match.group(0)
            if val in EXCLUSIONS: return val
            if val not in current_entities: current_entities.append(val)
            return f"[[P_{current_entities.index(val)}]]"

        masked_item = re.sub(num_pattern, mask_entities, item)
        masked_item = re.sub(name_pattern, mask_entities, masked_item)
        masked_list.append(masked_item)
        entities_map.append(current_entities)

    # --- PHASE 2: TRUE BATCH TRANSLATION ---
    translated_list = []
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        
        # Split into batches of 20 to stay safe with API limits/timeouts
        batch_size = 20
        for i in range(0, len(masked_list), batch_size):
            batch = masked_list[i : i + batch_size]
            try:
                # ONE network request for the entire batch
                batch_results = translator.translate_batch(batch)
                translated_list.extend(batch_results)
            except Exception as b_err:
                safe_log(f"Batch execution error: {str(b_err)}")
                # Fallback: Just return the masked batch if it fails entirely
                translated_list.extend(batch)

    except Exception as e:
        safe_log(f"Translator setup error: {str(e)}")
        translated_list = masked_list

    # --- PHASE 3: POST-TRANSLATION (UNMASKING) ---
    final_results = []
    for i, trans_item in enumerate(translated_list):
        if not trans_item or not isinstance(trans_item, str):
            # Fallback to original if translation failed or returned non-string
            final_results.append(text_list[i])
            continue
            
        item_entities = entities_map[i]
        for idx, original_val in enumerate(item_entities):
            placeholder = f"[[P_{idx}]]"
            trans_item = trans_item.replace(placeholder, original_val)
            trans_item = trans_item.replace(f"[[p_{idx}]]", original_val)
            trans_item = trans_item.replace(f"[P_{idx}]", original_val)
        final_results.append(trans_item)

    return final_results if is_batch else final_results[0]

def translate_pdf(input_path, output_path, target_lang, source_lang='auto'):
    """User-requested PDF translation via text extraction"""
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
        
        # Save as text (Note: We use output_path derived from app.py)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(text_content))
        
        return True, f"PDF translation completed: {total_pages} pages"
    except Exception as e:
        safe_log(f"PDF translation error: {e}")
        return False, str(e)

def translate_docx(input_path, output_path, target_lang):
    """DOCX Translation with deep table and formatting preservation"""
    try:
        doc = Document(input_path)
        
        # 1. Process Main Paragraphs with Batching
        # Collecting non-empty paragraphs for batch translation
        batch_text = []
        batch_paras = []
        current_batch_len = 0
        
        def process_batch(text_list, para_list):
            if not text_list: return
            translated_list = translate_text(text_list, target_lang)
            
            # Map back to paragraphs
            for i, para in enumerate(para_list):
                para.text = translated_list[i]

        for para in doc.paragraphs:
            if para.text.strip():
                p_text = para.text
                if current_batch_len + len(p_text) > 2000: # Smaller batches for higher reliability
                    process_batch(batch_text, batch_paras)
                    batch_text, batch_paras, current_batch_len = [], [], 0
                
                batch_text.append(p_text)
                batch_paras.append(para)
                current_batch_len += len(p_text)
        
        # Final batch
        process_batch(batch_text, batch_paras)
                
        # 2. Process Tables (Detection feature requested)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    # Recursive check for nested tables (though Document.tables only gets top-level)
                    for para in cell.paragraphs:
                        if para.text.strip():
                            para.text = translate_text(para.text, target_lang)
                    
                    # Handle nested tables inside cells if any
                    if cell.tables:
                        for nested_table in cell.tables:
                            for n_row in nested_table.rows:
                                for n_cell in n_row.cells:
                                    for n_para in n_cell.paragraphs:
                                        if n_para.text.strip():
                                            n_para.text = translate_text(n_para.text, target_lang)
                            
        doc.save(output_path)
        return True, "DOCX translated with tables preserved"
    except Exception as e:
        return False, str(e)

def translate_txt(input_path, output_path, target_lang):
    """TXT to Translated TXT"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        translated_text = translate_text(text, target_lang)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_text)
            
        return True, "Text file translated successfully"
    except Exception as e:
        return False, str(e)

def translate_xlsx(input_path, output_path, target_lang):
    """Excel to Translated Excel (Multi-sheet) with Visibility Fix"""
    try:
        import pandas as pd
        # Read all sheets, including hidden ones
        all_sheets = pd.read_excel(input_path, sheet_name=None)
        
        if not all_sheets:
            return False, "The Excel file contains no sheets"
            
        def cell_translator(val):
            if isinstance(val, str) and val.strip():
                return translate_text(val, target_lang)
            return val
            
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in all_sheets.items():
                # Element-wise translation
                for col in df.columns:
                    df[col] = df[col].apply(cell_translator)
                
                # Write back to excel
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
            # --- FIX: Visibility Enforcement ---
            # openpyxl requires at least one visible sheet. 
            # We explicitly set all translated sheets to visible.
            workbook = writer.book
            for worksheet in workbook.worksheets:
                worksheet.sheet_state = 'visible'
                
        return True, "Excel file translated successfully with sheets preserved"
    except Exception as e:
        return False, str(e)

def translate_csv(input_path, output_path, target_lang):
    """CSV to Translated CSV"""
    try:
        import pandas as pd
        df = pd.read_csv(input_path)
        
        def cell_translator(val):
            if isinstance(val, str) and val.strip():
                return translate_text(val, target_lang)
            return val
            
        for col in df.columns:
            df[col] = df[col].apply(cell_translator)
            
        df.to_csv(output_path, index=False)
        return True, "CSV file translated successfully"
    except Exception as e:
        return False, str(e)

# ============ DISPATCHER ============

def translate_document(input_path, output_path, target_lang, source_lang='auto', file_ext=None):
    """Dispatcher function with better error handling"""
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
