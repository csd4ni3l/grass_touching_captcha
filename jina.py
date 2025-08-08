from constants import JINA_URL, JINA_HEADERS
import requests, dotenv, os, sys, numpy as np

def get_embedding(input: list):
    headers = JINA_HEADERS

    if os.path.exists(".env"):
        dotenv.load_dotenv(".env")

    if not "JINA_TOKEN" in os.environ:
        print("Jina Token not found, exiting...")
        sys.exit(1)

    headers["Authorization"] = f"Bearer {os.environ['JINA_TOKEN']}"

    data = {
        "model": "jina-embeddings-v3",
        "input": input
    }

    response = requests.post(JINA_URL, headers=JINA_HEADERS, json=data)

    return [jina_object["embedding"] for jina_object in response.json()["data"]]

def get_grass_touching_similarity(image_url):
    grass_image_embedding, grass_word_embedding = get_embedding([image_url, "hand touching grass"])

    grass_image_embedding = np.array(grass_image_embedding)
    grass_word_embedding = np.array(grass_word_embedding)

    dot_product = np.dot(grass_image_embedding, grass_word_embedding)

    grass_image_mag = np.linalg.norm(grass_image_embedding)
    grass_word_mag = np.linalg.norm(grass_word_embedding)

    cosine_similarity = dot_product / (grass_image_mag * grass_word_mag)

    return cosine_similarity