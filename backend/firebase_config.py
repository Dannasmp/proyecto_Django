import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path

SERVICE_ACCOUNT_KEY_PATH = Path(__file__).resolve().parent / 'serviceAccountKey.json'


def get_firestore_client():
    if not firebase_admin._apps:
        cred = credentials.Certificate(str(SERVICE_ACCOUNT_KEY_PATH))
        firebase_admin.initialize_app(cred)
    return firestore.client()
