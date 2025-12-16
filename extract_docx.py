import zipfile
import re
import sys

def get_docx_text(path):
    try:
        with zipfile.ZipFile(path) as document:
            xml_content = document.read('word/document.xml').decode('utf-8')
            # Remove all tags
            text = re.sub('<[^>]+>', ' ', xml_content)
            # Clean up whitespace
            text = ' '.join(text.split())
            return text
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(get_docx_text(sys.argv[1]))
    else:
        print("Usage: python script.py <path_to_docx>")
