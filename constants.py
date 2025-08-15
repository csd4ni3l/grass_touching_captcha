import os

JINA_URL = 'https://api.jina.ai/v1/embeddings'
JINA_HEADERS = {
    'Content-Type': 'application/json',
}
RICKROLL_LINK = "https://www.youtube.com/watch?v=xvFZjo5PgG0"
UPLOAD_DIR = "uploads"
MINIMUM_COSINE_SIMILARITY = 0.65
WORD_TO_COMPARE = "hand touching grass"
DATABASE_FILE = "data.db"
MINIMUM_OCR_SIMILARITY = 0.7
OCR_CHALLENGE_LENGTH = 1

ACHIEVEMENTS = [
    [1, "I went outside!", "Brag to your friends with this one! You went outside the first time in your life. Continue on your journey."],
    [3, "Keeping up the streak!", "You went outside 3 times. Great job! (You should get one, btw)"],
    [7, "Out for a week!", "7 days of breathing fresh air, you're practically a nature veteran."],
    [14, "Two Weeks in the Wild", "Careful, you might be starting to get a tan."],
    [30, "One with the Outdoors", "An entire month! Are you sure you’re still a gamer?"],
    [50, "Grass Connoisseur", "You can now identify at least three different types of grass by touch alone."],
    [100, "Master of Chlorophyll", "The grass respects you now."],
    [200, "Photosynthesis Apprentice", "You spend so much time outside that plants start thinking you're one of them."],
    [365, "Solar-Powered", "A whole year of going outside, you've unlocked infinite vitamin D."],
    [500, "Grass Whisperer", "You hear the lawn speaking to you. It's weirdly supportive."],
    [1000, "Legendary Lawn Treader", "Songs will be sung of your bravery and your sandals."],
]

UPLOAD_DIR = os.path.join(os.getcwd(), UPLOAD_DIR)