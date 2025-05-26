import firebase_admin
from firebase_admin import credentials
import os

# Ortam değişkeni ile JSON yolu esnekleştirilebilir (isteğe bağlı)
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "app/lingualens-a8688-firebase-adminsdk-fbsvc-df225ff4f7.json")

# Firebase Admin SDK'yı başlat
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred)
