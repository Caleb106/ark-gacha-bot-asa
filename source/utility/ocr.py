import pytesseract

def output_screen(data):
    return pytesseract.image_to_string(data)