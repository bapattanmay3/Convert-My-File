import os
from pdf2docx import Converter
from PIL import Image
import PyPDF2

def convert_pdf_to_docx(input_path, output_path):
    """Convert PDF to DOCX"""
    try:
        cv = Converter(input_path)
        cv.convert(output_path)
        cv.close()
        return True, "Conversion successful"
    except Exception as e:
        return False, str(e)

def convert_image_to_pdf(input_path, output_path):
    """Convert Image to PDF"""
    try:
        image = Image.open(input_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(output_path, 'PDF')
        return True, "Conversion successful"
    except Exception as e:
        return False, str(e)

def convert_docx_to_pdf(input_path, output_path):
    """Convert DOCX to PDF (placeholder)"""
    try:
        import shutil
        shutil.copy(input_path, output_path)
        return True, "Conversion successful (placeholder)"
    except Exception as e:
        return False, str(e)
