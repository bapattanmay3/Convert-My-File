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

# Configure safe logging to avoid console encoding issues
logging.basicConfig(
    filename='translator.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def safe_log(msg):
    """Safely log error messages without crashing the console on Windows"""
    try:
        logging.error(msg)
    except:
        pass

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
    Translates text (or list of texts) with entity preservation.
    Native support for batch processing.
    """
    if not text:
        return "" if isinstance(text, str) else []
        
    is_batch = isinstance(text, list)
    text_list = text if is_batch else [text]
    results = []

    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        
        for original_item in text_list:
            if not original_item.strip():
                results.append(original_item)
                continue

            # --- PHASE 1: MASKING ---
            entities = []
            num_pattern = r'\b\d+(?:[.,]\d+)*\b'
            name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
            EXCLUSIONS = {'The', 'My', 'This', 'A', 'An', 'Our', 'Your', 'Their', 'His', 'Her', 'It', 'There', 'Where', 'When', 'Who', 'How', 'That', 'These', 'Those'}
            
            def mask_entities(match):
                val = match.group(0)
                if val in EXCLUSIONS: return val
                if val not in entities: entities.append(val)
                return f"[[P_{entities.index(val)}]]"

            masked_item = re.sub(num_pattern, mask_entities, original_item)
            masked_item = re.sub(name_pattern, mask_entities, masked_item)

            # --- PHASE 2: TRANSLATION ---
            try:
                # Use native translate for single items within the list loop logic
                # For ultra-performance we could use translate_batch on the MASKED list
                # but masking is per-item, so we'll do this safely.
                translated_item = translator.translate(masked_item)
                if translated_item is None: translated_item = masked_item
                
                # --- PHASE 3: UNMASKING ---
                for idx, original_val in enumerate(entities):
                    placeholder = f"[[P_{idx}]]"
                    translated_item = translated_item.replace(placeholder, original_val)
                    translated_item = translated_item.replace(f"[[p_{idx}]]", original_val)
                    translated_item = translated_item.replace(f"[P_{idx}]", original_val)
                
                results.append(translated_item)
            except Exception as e:
                safe_log(f"Batch item error: {str(e)}")
                results.append(original_item)

    except Exception as e:
        safe_log(f"Translator error: {str(e)}")
        return text

    return results if is_batch else results[0]

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
        success_render, msg_render = convert_docx_to_pdf(temp_docx_out, output_path)
        
        # Cleanup input bridge
        if os.path.exists(temp_docx_in):
            try: os.remove(temp_docx_in)
            except: pass
                
        if success_render:
            # Full success - cleanup bridge out and return PDF
            if os.path.exists(temp_docx_out):
                try: os.remove(temp_docx_out)
                except: pass
            return True, "PDF translated with structure preserved"
        else:
            # Partial success - handle DOCX fallback
            # Move the translated DOCX to the output path but change extension
            final_docx_path = output_path.replace('.pdf', '.docx')
            import shutil
            shutil.move(temp_docx_out, final_docx_path)
            # We return success=True but with a message explaining the format change
            # However, the app.py handles output_path, so we need to be careful.
            # Best is to return False with a specific 'PARTIAL' signal or just 
            # let translate_file handling it. Actually, app.py expects a file at output_path.
            # Let's just return False but with a directive message.
            return False, f"TRANS_DOCX_ONLY|{msg_render}"
        
    except Exception as e:
        return False, f"Bridge error: {str(e)}"

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
