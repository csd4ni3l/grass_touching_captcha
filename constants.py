import os

JINA_URL = 'https://api.jina.ai/v1/embeddings'
JINA_HEADERS = {
    'Content-Type': 'application/json',
}
RICKROLL_LINK = "https://www.youtube.com/watch?v=xvFZjo5PgG0"
UPLOAD_DIR = "uploads"
MINIMUM_COSINE_SIMILARITY = 0.75

UPLOAD_DIR = os.path.join(os.getcwd(), UPLOAD_DIR)