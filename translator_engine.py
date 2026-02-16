# Keep ONLY built-in imports at top
import os
import re
import time
import csv
# All other imports moved inside functions

# ===== GLOBAL LANGUAGES CONSTANT =====
LANGUAGES = {
    'af': 'Afrikaans', 'sq': 'Albanian', 'am': 'Amharic', 'ar': 'Arabic', 'hy': 'Armenian',
    'az': 'Azerbaijani', 'eu': 'Basque', 'be': 'Belarusian', 'bn': 'Bengali', 'bs': 'Bosnian',
    'bg': 'Bulgarian', 'ca': 'Catalan', 'ceb': 'Cebuano', 'ny': 'Chichewa', 'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)', 'co': 'Corsican', 'hr': 'Croatian', 'cs': 'Czech', 'da': 'Danish',
    'nl': 'Dutch', 'en': 'English', 'eo': 'Esperanto', 'et': 'Estonian', 'tl': 'Filipino',
    'fi': 'Finnish', 'fr': 'French', 'fy': 'Frisian', 'gl': 'Galician', 'ka': 'Georgian',
    'de': 'German', 'el': 'Greek', 'gu': 'Gujarati', 'ht': 'Haitian Creole', 'ha': 'Hausa',
    'haw': 'Hawaiian', 'iw': 'Hebrew', 'hi': 'Hindi', 'hmn': 'Hmong', 'hu': 'Hungarian',
    'is': 'Icelandic', 'ig': 'Igbo', 'id': 'Indonesian', 'ga': 'Irish', 'it': 'Italian',
    'ja': 'Japanese', 'jw': 'Javanese', 'kn': 'Kannada', 'kk': 'Kazakh', 'km': 'Khmer',
    'ko': 'Korean', 'ku': 'Kurdish (Kurmanji)', 'ky': 'Kyrgyz', 'lo': 'Lao', 'la': 'Latin',
    'lv': 'Latvian', 'lt': 'Lithuanian', 'lb': 'Luxembourgish', 'mk': 'Macedonian', 'mg': 'Malagasy',
    'ms': 'Malay', 'ml': 'Malayalam', 'mt': 'Maltese', 'mi': 'Maori', 'mr': 'Marathi',
    'mn': 'Mongolian', 'my': 'Myanmar (Burmese)', 'ne': 'Nepali', 'no': 'Norwegian', 'ps': 'Pashto',
    'fa': 'Persian', 'pl': 'Polish', 'pt': 'Portuguese', 'pa': 'Punjabi', 'ro': 'Romanian',
    'ru': 'Russian', 'sm': 'Samoan', 'gd': 'Scots Gaelic', 'sr': 'Serbian', 'st': 'Sesotho',
    'sn': 'Shona', 'sd': 'Sindhi', 'si': 'Sinhala', 'sk': 'Slovak', 'sl': 'Slovenian',
    'so': 'Somali', 'es': 'Spanish', 'su': 'Sundanese', 'sw': 'Swahili', 'sv': 'Swedish',
    'tg': 'Tajik', 'ta': 'Tamil', 'te': 'Telugu', 'th': 'Thai', 'tr': 'Turkish',
    'uk': 'Ukrainian', 'ur': 'Urdu', 'uz': 'Uzbek', 'vi': 'Vietnamese', 'cy': 'Welsh',
    'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba', 'zu': 'Zulu'
}

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

def clean_text(text):
    """Normalize text by removing redundant whitespace and fixing spaced-out PDF text"""
    if not text: return ""
    # Replace null bytes
    text = text.replace('\x00', '')
    
    # Handle spaced-out text (e.g. "P r o t e c t e d") which confuses translators
    # Heuristic: If we see a pattern of [Letter][Space][Letter][Space]
    if len(text) > 10:
        # Use regex to find sequences of single letters separated by spaces
        # e.g., "H e l l o" -> "Hello"
        spaced_pattern = r'(?:(?<=\s)|(?<=^))([a-zA-Z0-9])\s+(?=([a-zA-Z0-9])(?:\s|$))'
        # Group 1 is the character. We replace the character + space with just the character.
        text = re.sub(spaced_pattern, r'\1', text)
    
    # Final normalization
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

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

# ===== TRANSLATE FUNCTION USING TRANSLATORS LIBRARY =====
def translate_text(text, target_lang, source_lang='auto', max_retries=3):
    """Safe translation with UTF-8 preservation"""
    from deep_translator import GoogleTranslator  # ✅ ADD THIS
    if not text or should_preserve(text):
        return text
    
    # Ensure text is properly encoded
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')
    
    # Normalize text (keeping my de-spacing logic too as it proved useful)
    text = clean_text(text)
    
    target = target_lang[:2] # Ensure we use 2-char code for deep-translator
    
    chunk_size = 4000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    translated_chunks = []
    
    for chunk in chunks:
        for attempt in range(max_retries):
            try:
                translator = GoogleTranslator(source=source_lang, target=target)
                result = translator.translate(chunk)
                if result:
                    # Force UTF-8
                    if isinstance(result, str):
                        result = result.encode('utf-8').decode('utf-8')
                    translated_chunks.append(result)
                    break
                time.sleep(1)
            except Exception as e:
                try:
                    print(f"Translation attempt {attempt+1} failed: {e}")
                except UnicodeEncodeError:
                    pass
                if attempt == max_retries - 1:
                    # Fallback with UTF-8 encoding
                    fallback = chunk.encode('utf-8').decode('utf-8')
                    translated_chunks.append(fallback)
                time.sleep(2)
    
    return ' '.join(translated_chunks)

def is_valid_translation(translated_text, target_lang, original_text=None):
    """
    Check if the translation is valid for the target language.
    1. For languages with distinct scripts, checks Unicode ranges.
    2. For Latin-based languages, checks if it's different from original (if provided).
    """
    if not translated_text:
        return False
    
    target = target_lang.split('-')[0].lower()
    
    # Script-based validation mapping
    script_ranges = {
        'hi': ('\u0900', '\u097F'),  # Devanagari (Hindi, Marathi, etc.)
        'bn': ('\u0980', '\u09FF'),  # Bengali
        'ar': ('\u0600', '\u06FF'),  # Arabic
        'fa': ('\u0600', '\u06FF'),  # Persian
        'ur': ('\u0600', '\u06FF'),  # Urdu
        'ru': ('\u0400', '\u04FF'),  # Cyrillic (Russian, etc.)
        'uk': ('\u0400', '\u04FF'),  # Ukrainian
        'be': ('\u0400', '\u04FF'),  # Belarusian
        'el': ('\u0370', '\u03FF'),  # Greek
        'iw': ('\u0590', '\u05FF'),  # Hebrew
        'he': ('\u0590', '\u05FF'),  # Hebrew (alternative code)
        'ja': ('\u3040', '\u9FFF'),  # Japanese (Hiragana/Katakana/Kanji)
        'zh': ('\u4E00', '\u9FFF'),  # Chinese (CJK Unified Ideographs)
        'ko': ('\uAC00', '\uD7AF'),  # Korean (Hangul)
        'ta': ('\u0B80', '\u0BFF'),  # Tamil
        'te': ('\u0C00', '\u0C7F'),  # Telugu
        'kn': ('\u0C80', '\u0CFF'),  # Kannada
        'ml': ('\u0D00', '\u0D7F'),  # Malayalam
        'gu': ('\u0A80', '\u0AFF'),  # Gujarati
        'pa': ('\u0A00', '\u0A7F'),  # Punjabi
        'th': ('\u0E00', '\u0E7F'),  # Thai
    }
    
    if target in script_ranges:
        low, high = script_ranges[target]
        chars_in_range = sum(1 for c in translated_text if low <= c <= high)
        return chars_in_range > len(translated_text.strip()) * 0.2  # 20% threshold
    
    # For Latin-based or others, check if it's different from original
    if original_text:
        # Simple similarity check: if they are identical, it's likely failed
        if translated_text.strip() == original_text.strip() and len(original_text) > 10:
            return False
            
    return True

# ===== PDF TRANSLATOR (pdfplumber) =====
def translate_pdf(input_path, output_path, target_lang, source_lang='auto'):
    """Translate PDF using pdfplumber for cleaner text extraction"""
    import PyPDF2  # ✅ ADD THIS
    import pdfplumber
    try:
        text_content = []
        # Update output path early for consistency
        output_txt = output_path if output_path.endswith('.txt') else output_path.replace('.pdf', '.txt')
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_txt), exist_ok=True)
        
        with pdfplumber.open(input_path) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                try:
                    print(f"Translating page {i+1}/{total_pages}")
                except UnicodeEncodeError:
                    pass
                
                text = page.extract_text()
                if text and text.strip():
                    translated = translate_text(text, target_lang, source_lang)
                    # Force UTF-8 encoding check for reliability
                    if isinstance(translated, str):
                        translated = translated.encode('utf-8', errors='ignore').decode('utf-8')
                    text_content.append(translated)
                else:
                    text_content.append("")
        
        # Write translated text with UTF-8 BOM for better Windows compatibility
        with open(output_txt, 'w', encoding='utf-8-sig') as f:
            f.write('\n\n'.join(text_content))
        
        # Verify the file was written correctly
        try:
            with open(output_txt, 'r', encoding='utf-8-sig') as f:
                verification = f.read(100)
                print(f"Verification - First 100 chars: {repr(verification)}")
        except Exception as ve:
            print(f"Verification step failed: {ve}")
            
        return True, f"PDF translation completed: {total_pages} pages", output_txt
    except Exception as e:
        try:
            print(f"PDF translation error: {e}")
            import traceback
            traceback.print_exc()
        except UnicodeEncodeError:
            print(f"PDF translation error: [Unicode Error]")
        return False, str(e), output_path

# ===== WORD DOCUMENT TRANSLATOR =====
def translate_docx(input_path, output_path, target_lang, source_lang='auto'):
    """Translate Word document preserving structure"""
    from docx import Document  # ✅ ADD THIS
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
    """Translate Excel files preserving structure"""
    import openpyxl  # ✅ ADD THIS
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
        with open(input_path, 'r', encoding='utf-8-sig') as infile:
            reader = csv.reader(infile)
            rows = list(reader)
        
        translated_rows = []
        for row in rows:
            new_row = []
            for cell in row:
                if should_preserve(cell):
                    new_row.append(cell)
                else:
                    new_row.append(translate_text(cell, target_lang, source_lang))
            translated_rows.append(new_row)
            
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as outfile:
            writer = csv.writer(outfile)
            writer.writerows(translated_rows)
        return True, "CSV translation completed"
    except Exception as e:
        return False, str(e)

# ===== TEXT FILE TRANSLATOR =====
def translate_text_file(input_path, output_path, target_lang, source_lang='auto'):
    """Translate plain text files"""
    try:
        with open(input_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        translated = translate_text(content, target_lang, source_lang)
        
        # Force UTF-8 with BOM
        with open(output_path, 'w', encoding='utf-8-sig') as f:
            f.write(translated)
        return True, "Text translation completed"
    except Exception as e:
        try:
            print(f"Text translation error: {e}")
        except UnicodeEncodeError:
            pass
        return False, str(e)

# ===== MAIN DISPATCHER FUNCTION =====
def translate_document(input_path, output_path, target_lang, source_lang='auto', file_ext=None):
    """Main dispatcher for document translation"""
    if file_ext is None:
        file_ext = os.path.splitext(input_path)[1].lower()
    
    # Map extensions to translator functions
    translators_map = {
        '.pdf': translate_pdf,
        '.docx': translate_docx,
        '.doc': translate_docx,
        '.xlsx': translate_excel,
        '.xls': translate_excel,
        '.csv': translate_csv,
        '.txt': translate_text_file,
    }
    
    translator_func = translators_map.get(file_ext)
    if translator_func:
        # For PDF, the output is always TXT in this basic engine (unless using premium tools)
        if file_ext == '.pdf':
            output_path = output_path.replace('.pdf', '.txt')
            
        success, message = translator_func(input_path, output_path, target_lang, source_lang)
        return success, message, output_path
    else:
        return False, f"Unsupported file type: {file_ext}", output_path

# Backward compatibility (some files might still call translate_file)
def translate_file(input_path, output_path, target_lang, source_lang='auto'):
    return translate_document(input_path, output_path, target_lang, source_lang)