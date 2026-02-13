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
    Translates text with entity preservation (names/numbers).
    Uses placeholders to protect specific entities from the translation engine.
    """
    if not text.strip():
        return ""
        
    # --- PHASE 1: MASKING ---
    # Patterns to protect: 
    # 1. Numbers (including decimals and commas)
    # 2. Capitalized words (likely names/brands), excluding start of sentences if possible
    # We use a broad regex for numbers and a heuristic for names.
    
    # Identify unique entities
    entities = []
    
    # Protect numbers: e.g. 100, 10.5, 1,000, 2024
    num_pattern = r'\b\d+(?:[.,]\d+)*\b'
    # Protect capitalized words that aren't entirely uppercase (to avoid acronyms which might need translation)
    # This is a heuristic for names/proper nouns.
    name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    
    # Common words that shouldn't be masked even if capitalized (heuristic)
    EXCLUSIONS = {'The', 'My', 'This', 'A', 'An', 'Our', 'Your', 'Their', 'His', 'Her', 'It', 'There', 'Where', 'When', 'Who', 'How', 'That', 'These', 'Those'}
    
    def mask_entities(match):
        val = match.group(0)
        # Avoid masking common starters if they are at the beginning of a block
        if val in EXCLUSIONS:
            return val
            
        if val not in entities:
            entities.append(val)
        idx = entities.index(val)
        return f"[[P_{idx}]]"

    # Mask numbers first (very reliable)
    masked_text = re.sub(num_pattern, mask_entities, text)
    # Mask names/proper nouns (heuristic: Capitalized words)
    masked_text = re.sub(name_pattern, mask_entities, masked_text)

    # --- PHASE 2: TRANSLATION ---
    translator = GoogleTranslator(source=source_lang, target=target_lang)
    
    # Split text into chunks of 4500 characters
    chunk_size = 4500
    chunks = [masked_text[i:i+chunk_size] for i in range(0, len(masked_text), chunk_size)]
    
    translated_chunks = []
    for chunk in chunks:
        try:
            # Google Translate handles [[P_0]] style placeholders well (usually ignores them)
            translated_chunks.append(translator.translate(chunk))
        except Exception as e:
            print(f"Translation chunk error: {e}")
            translated_chunks.append(chunk)
            
    translated_text = "".join(translated_chunks)

    # --- PHASE 3: UNMASKING ---
    # Restore the original entities
    for idx, original_val in enumerate(entities):
        placeholder = f"[[P_{idx}]]"
        # Some translators might remove brackets or change casing of placeholders, 
        # so we do a few common variations just in case.
        translated_text = translated_text.replace(placeholder, original_val)
        # Fallbacks for minor engine mutations
        translated_text = translated_text.replace(f"[[p_{idx}]]", original_val)
        translated_text = translated_text.replace(f"[P_{idx}]", original_val)
        
    return translated_text

def translate_pdf(input_path, output_path, target_lang):
    """
    Enhanced PDF Translation via Bridge Workflow:
    PDF -> DOCX (Layout Restoration) -> Translate -> PDF (Render)
    """
    try:
        from converter_universal import convert_pdf_to_docx, convert_docx_to_pdf
        import uuid
        
        unique_id = str(uuid.uuid4())
        folder = os.path.dirname(input_path)
        
        # Step 1: PDF to DOCX
        temp_docx_in = os.path.join(folder, f"bridge_in_{unique_id}.docx")
        success, msg = convert_pdf_to_docx(input_path, temp_docx_in)
        if not success:
            return False, f"Structural analysis failed: {msg}"
            
        # Step 2: Translate DOCX
        temp_docx_out = os.path.join(folder, f"bridge_out_{unique_id}.docx")
        success, msg = translate_docx(temp_docx_in, temp_docx_out, target_lang)
        if not success:
            return False, f"Content translation failed: {msg}"
            
        # Step 3: DOCX to PDF
        success, msg = convert_docx_to_pdf(temp_docx_out, output_path)
        
        # Cleanup
        for tmp in [temp_docx_in, temp_docx_out]:
            if os.path.exists(tmp):
                try: os.remove(tmp)
                except: pass
                
        if success:
            return True, "PDF translated with structure preserved"
        return False, f"Final rendering failed: {msg}"
        
    except Exception as e:
        return False, f"Bridge error: {str(e)}"

def translate_docx(input_path, output_path, target_lang):
    """DOCX Translation with deep table and formatting preservation"""
    try:
        doc = Document(input_path)
        
        # 1. Process Main Paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                # We translate at the paragraph level but try to keep runs 
                # (Simple approach: replace whole paragraph text)
                # For better results while keeping format, one could translate runs 
                # but Google Translate needs context, so paragraph level is safer.
                original_text = para.text
                translated_text = translate_text(original_text, target_lang)
                para.text = translated_text
                
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
    """Excel to Translated Excel (Multi-sheet)"""
    try:
        import pandas as pd
        # Read all sheets
        all_sheets = pd.read_excel(input_path, sheet_name=None)
        
        def cell_translator(val):
            if isinstance(val, str) and val.strip():
                return translate_text(val, target_lang)
            return val
            
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in all_sheets.items():
                # Element-wise translation
                # Use applymap for older pandas or map for newer, but apply works across columns
                for col in df.columns:
                    df[col] = df[col].apply(cell_translator)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
        return True, "Excel file translated successfully"
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

TRANSLATORS = {
    'pdf': translate_pdf,
    'docx': translate_docx,
    'txt': translate_txt,
    'xlsx': translate_xlsx,
    'xls': translate_xlsx, # xlrd/openpyxl handled by pandas
    'csv': translate_csv
}

def translate_file(input_path, output_path, ext, target_lang):
    """Main entry point for file translation"""
    ext = ext.lower().replace('.', '')
    if ext in TRANSLATORS:
        return TRANSLATORS[ext](input_path, output_path, target_lang)
    else:
        return False, f"File format {ext} not supported for translation"
