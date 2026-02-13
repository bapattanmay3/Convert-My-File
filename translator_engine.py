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

def translate_text(text, target_lang, source_lang='auto'):
    """Translates text in chunks to avoid API limits (approx 5000 chars)"""
    if not text.strip():
        return ""
        
    translator = GoogleTranslator(source=source_lang, target=target_lang)
    
    # Split text into chunks of 4500 characters
    chunk_size = 4500
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    translated_chunks = []
    for chunk in chunks:
        try:
            translated_chunks.append(translator.translate(chunk))
        except Exception as e:
            print(f"Translation chunk error: {e}")
            translated_chunks.append(chunk) # Fallback to original
            
    return "".join(translated_chunks)

def translate_pdf(input_path, output_path, target_lang):
    """PDF to Translated TXT (Layout preservation is complex, focus on text for now)"""
    try:
        with open(input_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        translated_text = translate_text(text, target_lang)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_text)
            
        return True, "PDF translated successfully to text"
    except Exception as e:
        return False, str(e)

def translate_docx(input_path, output_path, target_lang):
    """DOCX to Translated DOCX (Attempt to preserve structure)"""
    try:
        doc = Document(input_path)
        
        for para in doc.paragraphs:
            if para.text.strip():
                para.text = translate_text(para.text, target_lang)
                
        # Handle tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        cell.text = translate_text(cell.text, target_lang)
                        
        doc.save(output_path)
        return True, "DOCX translated successfully"
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

# ============ DISPATCHER ============

TRANSLATORS = {
    'pdf': translate_pdf,
    'docx': translate_docx,
    'txt': translate_txt
}

def translate_file(input_path, output_path, ext, target_lang):
    """Main entry point for file translation"""
    ext = ext.lower().replace('.', '')
    if ext in TRANSLATORS:
        return TRANSLATORS[ext](input_path, output_path, target_lang)
    else:
        return False, f"File format {ext} not supported for translation"
