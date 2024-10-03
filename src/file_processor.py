import tempfile
import json
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import fitz  # PyMuPDF
from docx import Document


def get_raw_text(file, path: str):
    stop_words = set(stopwords.words("english"))

    def process_text(text):
        words = word_tokenize(text)
        filtered_words = [
            {"word": word, "count": words.count(word)}
            for word in words
            if word.lower() not in stop_words
        ]
        return filtered_words

    if path.endswith(".txt"):
        filecontent = file.read()
        return process_text(filecontent.decode("utf-8"))

    elif path.endswith(".pdf"):
        with tempfile.TemporaryFile() as temp_pdf:
            temp_pdf.write(file.read())
            temp_pdf.seek(0)
            doc = fitz.open(stream=temp_pdf.read(), filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
        return process_text(text)

    elif path.endswith(".docx") or path.endswith(".doc"):
        with tempfile.TemporaryFile() as temp_docx:
            temp_docx.write(file.read())
            temp_docx.seek(0)
            doc = Document(temp_docx)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        return process_text(text)

    else:
        raise ValueError("Unsupported file type")
