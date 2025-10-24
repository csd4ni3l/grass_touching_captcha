import easyocr, difflib, random, string
from constants import OCR_CHALLENGE_LENGTH

reader = easyocr.Reader(['en'])

def check_text_similarity(image_path, text):
    result = reader.readtext(image_path, allowlist=string.ascii_letters + string.digits)
    image_text = ''.join([text[1] for text in result]).lower()
    similarity = difflib.SequenceMatcher(None, text, image_text).ratio()
    return image_text, similarity

def generate_challenge(username):
    return f"{username} {''.join([str(random.randint(0, 10)) for _ in range(OCR_CHALLENGE_LENGTH)])}"