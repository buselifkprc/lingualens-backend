from flask import Blueprint, request, jsonify
from app.database import db_session
from app.models.user import User
from app.models.translation import Translation
from app.models.review import Review
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
import os
import uuid
import requests
from dotenv import load_dotenv
from firebase_admin import auth  
import base64

load_dotenv() # .env dosyasını yükle
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

bp = Blueprint('routes', __name__)

# Yelp API Anahtarını .env dosyasından al
# .env dosyasında YELP_API_KEY=YOUR_YELP_API_KEY şeklinde bir satır olduğundan emin ol
YELP_API_KEY = os.getenv("YELP_API_KEY")

# Kullanıcı profili
@bp.route("/profile/<int:user_id>", methods=["GET"])
def get_profile(user_id):
    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "surname": user.surname,
        "profile_image": user.profile_image
    }), 200 

# Kayıt
@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Missing fields"}), 400

    if db_session.query(User).filter_by(email=data["email"]).first():
        return jsonify({"error": "User already exists"}), 409

    hashed_pw = generate_password_hash(data["password"])
    new_user = User(
        email=data["email"],
        password=hashed_pw,
        name=data.get("name", ""),
        surname=data.get("surname", ""),
        profile_image=data.get("profile_image", "")
    )
    db_session.add(new_user)
    db_session.commit()
    return jsonify({"message": "User registered successfully"}), 201

# Giriş
@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    print(f"Login isteği alındı. Veri: {data}") # DEBUG: Gelen veriyi yazdır

    if not data or not data.get("email") or not data.get("password"):
        print("Hata: Eksik alanlar") # DEBUG
        return jsonify({"error": "Missing fields"}), 400

    user = db_session.query(User).filter_by(email=data["email"]).first()
    if not user:
        print(f"Hata: Kullanıcı bulunamadı. E-posta: {data.get('email')}") # DEBUG
        return jsonify({"error": "User not found"}), 404

    print(f"Kullanıcı bulundu: ID={user.id}, E-posta={user.email}, Şifre Hash={user.password[:10]}...") # DEBUG

    # Firebase kullanıcısı kontrolü
    if user.password == "firebase-auth":
        print("Firebase kullanıcı girişi.") # DEBUG
        # Mobil uygulama ve backend senkronizasyonu için, backend'in Firebase Auth ile giriş yapan kullanıcıyı
        # kendi veritabanına kaydederken şifresini 'firebase-auth' olarak işaretlemesi beklenir.
        # Bu durumda, frontend'den gönderilen 'firebase-auth-dummy-password' ile eşleşmesi beklenir.
        # Ancak burada önemli olan, mobil uygulamanın zaten Firebase ile kimlik doğrulamasını yapmış olmasıdır.
        # Web tarafında ise, Firebase ile giriş yapan kullanıcı için backend'e bildirim yapıp
        # backend'deki kullanıcı ID'sini almak önemlidir.
        return jsonify({
            "message": "Firebase login successful",
            "user_id": user.id,
            "name": user.name,
            "surname": user.surname
        }), 200

    # Normal kullanıcı kontrolü
    # print(f"Normal kullanıcı girişi denemesi. Girilen şifre: {data['password']}") # Şifreyi loglamaktan kaçın!
    if not check_password_hash(user.password, data["password"]):
        print("Hata: Geçersiz kimlik bilgileri (şifre yanlış).") # DEBUG
        return jsonify({"error": "Invalid credentials"}), 401 # <--- BURASI ÇOK ÖNEMLİ: Hata durumunda 401 dönmeli!

    print("Başarılı giriş: Kullanıcı kimlik bilgileri doğru.") # DEBUG
    return jsonify({
        "message": "Login successful",
        "user_id": user.id,
        "name": user.name,
        "surname": user.surname
    }), 200


# Çeviri ekleme
@bp.route("/translations", methods=["POST"])
def add_translation():
    data = request.get_json()
    required_fields = ("user_id", "original_text", "target_language", "translated_text")
    if not data or not all(k in data for k in required_fields):
        return jsonify({"error": "Eksik alanlar var"}), 400

    new_translation = Translation(
        user_id=data["user_id"],
        original_text=data["original_text"],
        target_language=data["target_language"],
        translated_text=data["translated_text"]
    )

    db_session.add(new_translation)
    db_session.commit()

    return jsonify({"message": "Çeviri başarıyla kaydedildi"}), 201
    

# Kullanıcının çeviri geçmişi
@bp.route("/translations/<int:user_id>", methods=["GET"])
def get_translations(user_id):
    translations = db_session.query(Translation).filter_by(user_id=user_id).all()
    
    result = []
    for t in translations:
        result.append({
            "id": t.id,
            "original_text": t.original_text,
            "target_language": t.target_language,
            "created_at": t.created_at.isoformat()
        })
    
    return jsonify(result), 200

# Yorum ekleme
@bp.route("/reviews", methods=["POST"])
def add_review():
    data = request.get_json()
    required = ["user_id", "restaurant_name", "address", "rating", "review_text"]

    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    new_review = Review(
        user_id=data["user_id"],
        restaurant_name=data["restaurant_name"],
        address=data["address"],
        rating=data["rating"],
        review_text=data["review_text"]
    )

    db_session.add(new_review)
    db_session.commit()

    return jsonify({"message": "Review saved successfully"}), 201

# Kullanıcının yorum geçmişi
@bp.route("/reviews/<int:user_id>", methods=["GET"])
def get_reviews(user_id):
    reviews = db_session.query(Review).filter_by(user_id=user_id).all()
    
    result = []
    for r in reviews:
        result.append({
            "id": r.id,
            "restaurant_name": r.restaurant_name,
            "address": r.address,
            "rating": float(r.rating),
            "review_text": r.review_text,
            "visited_at": r.visited_at.isoformat()
        })
    
    return jsonify(result), 200

# Yelp API (Şimdi Gerçek Veri Çekecek)
@bp.route("/restaurant-search", methods=["GET"])
def restaurant_search():
    term = request.args.get("term")
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")

    if not all([term, latitude, longitude]):
        return jsonify({"error": "Missing query parameters (term, latitude, longitude)"}), 400

    if not YELP_API_KEY:
        return jsonify({"error": "YELP_API_KEY not found in .env file"}), 500

    headers = {
        "Authorization": f"Bearer {YELP_API_KEY}"
    }
    params = {
        "term": term,
        "latitude": latitude,
        "longitude": longitude,
        "limit": 1 # Sadece ilk sonucu al
    }
    
    YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"

    try:
        response = requests.get(YELP_SEARCH_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status() # HTTP hataları için istisna fırlatır

        yelp_data = response.json()
        return jsonify(yelp_data), 200
    except requests.exceptions.RequestException as e:
        print(f"Yelp Search API Hatası: {e}")
        return jsonify({"error": f"Failed to fetch restaurant data from Yelp: {str(e)}"}), 500


# Yeni Endpoint: Yelp API'den Restoran Yorumlarını Çekme
@bp.route("/restaurant-reviews/<string:restaurant_id>", methods=["GET"])
def get_restaurant_reviews(restaurant_id):
    if not restaurant_id:
        return jsonify({"error": "Missing restaurant_id"}), 400

    if not YELP_API_KEY:
        return jsonify({"error": "YELP_API_KEY not found in .env file"}), 500

    headers = {
        "Authorization": f"Bearer {YELP_API_KEY}"
    }
    
    YELP_REVIEWS_URL = f"https://api.yelp.com/v3/businesses/{restaurant_id}/reviews"

    try:
        response = requests.get(YELP_REVIEWS_URL, headers=headers, timeout=10)
        response.raise_for_status()

        yelp_data = response.json()
        return jsonify(yelp_data), 200
    except requests.exceptions.RequestException as e:
        print(f"Yelp Reviews API Hatası: {e}")
        return jsonify({"error": f"Failed to fetch reviews from Yelp: {str(e)}"}), 500


# OCR endpoint (mobil ve web uyumlu)
@bp.route("/photo-ocr", methods=["POST"])
def photo_ocr():
    print("OCR endpoint'e istek geldi")
    print("Gelen dosyalar:", request.files)
    
    if 'image' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    image = request.files['image']
    filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    image.save(filepath)

    try:
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img)

        return jsonify({
            'message': 'OCR success',
            'filename': filename,
            'text': text
        }), 200
    except Exception as e:
        print("OCR Hatası:", e)
        return jsonify({'error': str(e)}), 500


# Profil resmi yükleme
@bp.route("/profile-image", methods=["POST"])
def upload_profile_image():
    if 'user_id' not in request.form or 'image' not in request.files:
        return jsonify({"error": "Eksik veri"}), 400

    user_id = request.form["user_id"]
    image = request.files["image"]

    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 404

    # Görseli base64 olarak kaydet
    import base64
    image_data = base64.b64encode(image.read()).decode('utf-8')
    user.profile_image = f"data:{image.mimetype};base64,{image_data}"
    db_session.commit()

    return jsonify({"message": "Profil fotoğrafı kaydedildi"}), 200

# Firebase kullanıcılarını veritabanına aktırma
@bp.route("/sync-firebase-users", methods=["POST"])
def sync_firebase_users():
    try:
        users = auth.list_users().iterate_all()
        added = 0
        skipped = 0

        for firebase_user in users:
            email = firebase_user.email
            if not email:
                continue

            existing = db_session.query(User).filter_by(email=email).first()
            if existing:
                skipped += 1
                continue

            name = firebase_user.display_name.split(" ")[0] if firebase_user.display_name else ""
            surname = firebase_user.display_name.split(" ")[1] if firebase_user.display_name and " " in firebase_user.display_name else ""

            # Şifre zorunlu olduğu için dummy bir şifre kullanılıyor (login işleminde etkili değil)
            new_user = User(
                email=email,
                password="firebase-auth",  # NOT NULL hatasını önlemek için
                name=name,
                surname=surname,
                profile_image=""
            )
            db_session.add(new_user)
            added += 1

        db_session.commit()
        return jsonify({
            "message": f"{added} kullanıcı eklendi, {skipped} kullanıcı zaten vardı."
        }), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500 
@bp.route("/change-password", methods=["POST"])
def change_password():
    data = request.get_json()
    user_id = data.get("user_id")
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not user_id or not current_password or not new_password:
        return jsonify({"error": "Eksik alanlar"}), 400

    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 404

    if user.password == "firebase-auth":
        return jsonify({"error": "Firebase kullanıcıları şifre değiştiremez."}), 403

    if not check_password_hash(user.password, current_password):
        return jsonify({"error": "Mevcut şifre hatalı"}), 401

    user.password = generate_password_hash(new_password)
    db_session.commit()

    return jsonify({"message": "Şifre başarıyla güncellendi"}), 200

@bp.route("/delete-user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 404

    db_session.delete(user)
    db_session.commit()

    return jsonify({"message": "Kullanıcı başarıyla silindi"}), 200
# Çeviri işlemi için LibreTranslate API'ye istek atan endpoint
@bp.route("/translate", methods=["POST"])
def translate_text():
    data = request.get_json()
    print(f"Gelen çeviri isteği verisi: {data}") # DEBUG: Gelen veriyi yazdır
    if not data or "text" not in data or "target_lang" not in data:
        print("Hata: Eksik alanlar") # DEBUG
        return jsonify({"error": "Eksik alanlar"}), 400

    try:
        # LibreTranslate API'ye gönderilecek veriyi oluştur
        translate_payload = {
            "q": data["text"],
            "source": "auto",
            "target": data["target_lang"],
            "format": "text"
        }
        print(f"LibreTranslate API'ye gönderilen veri: {translate_payload}") # DEBUG

        response = requests.post("http://localhost:5050/translate", json=translate_payload, timeout=10)
        
        print(f"LibreTranslate API'den HTTP durum kodu: {response.status_code}") # DEBUG: Durum kodunu yazdır
        response.raise_for_status() # HTTP hataları için istisna fırlatır (örn: 4xx veya 5xx)

        translated = response.json()
        print(f"LibreTranslate API'den gelen ham yanıt: {translated}") # DEBUG: API'den gelen ham yanıtı yazdır

        # LibreTranslate API'nin yanıtında "translatedText" anahtarını bekliyoruz
        translated_text_content = translated.get("translatedText", "")
        if not translated_text_content:
            print("Hata: LibreTranslate yanıtında 'translatedText' bulunamadı veya boş.") # DEBUG
            return jsonify({"error": "Çeviri yanıtı geçersiz veya boş"}), 500

        return jsonify({
            "translated_text": translated_text_content # Flask'ın döndürdüğü anahtar 'translated_text' (snake_case)
        }), 200
    except requests.exceptions.Timeout:
        print("Hata: LibreTranslate API zaman aşımına uğradı.")
        return jsonify({"error": "Çeviri hizmeti zaman aşımına uğradı, lütfen tekrar deneyin."}), 500
    except requests.exceptions.RequestException as e:
        print(f"LibreTranslate API Hatası: {e}")
        # Hata durumunda LibreTranslate API'den gelen yanıtı da loglayabiliriz
        if hasattr(e, 'response') and e.response is not None:
            print(f"LibreTranslate API Hata Yanıtı: {e.response.text}")
        return jsonify({"error": f"Çeviri hizmetiyle iletişim hatası: {str(e)}"}), 500
    except Exception as e:
        print(f"Genel Çeviri Hatası: {e}")
        return jsonify({"error": f"Sunucu tarafında beklenmeyen hata: {str(e)}"}),