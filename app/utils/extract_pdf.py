import fitz  # PyMuPDF
from fastapi import UploadFile

async def extract_text_from_upload(file: UploadFile):
    
    pdf_bytes = await file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    return text