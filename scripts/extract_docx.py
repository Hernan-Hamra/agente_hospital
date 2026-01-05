#!/usr/bin/env python3
import sys
from docx import Document

def extract_text(docx_path):
    doc = Document(docx_path)
    text = []
    for para in doc.paragraphs:
        text.append(para.text)
    return '\n'.join(text)

if __name__ == '__main__':
    print(extract_text(sys.argv[1]))
