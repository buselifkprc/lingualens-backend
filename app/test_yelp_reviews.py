import requests
import os
from dotenv import load_dotenv

# .env dosyasını yükle (YELP_API_KEY burada olmalı)
load_dotenv()

YELP_API_KEY = os.getenv("YELP_API_KEY")

if not YELP_API_KEY:
    print("Hata: YELP_API_KEY .env dosyasında bulunamadı.")
    exit()

# Uygulamadan gelen Burger King ID'si
# Ekran Resmi 2025-05-24 22.45.46.png görselinden aldım: 2L4Tj-kfHaBx1F1nwDz-_A
# Veya test etmek istediğin başka bir restaurant ID'si
restaurant_id_to_test = "starbucks-san-francisco-166"

# Popüler ve kesin yorumu olan bir yer ID'si ile de deneyebiliriz (Örn: San Francisco'daki bir yer)
# restaurant_id_to_test = "gC9K3Y2Xp4bF5k8N9d1A8Q" # Örnek bir ID, bunu Yelp'ten bulman gerekebilir
# restaurant_id_to_test = "WavvLdfdP6g8nZLzJRSWSQ" # Example: A local cafe in Elazığ if you find one with an ID that works on Yelp

YELP_REVIEWS_URL = f"https://api.yelp.com/v3/businesses/{restaurant_id_to_test}/reviews"

headers = {
    "Authorization": f"Bearer {YELP_API_KEY}"
}

print(f"Yelp API Yorumlar URL: {YELP_REVIEWS_URL}")
print(f"Kullanılan API Anahtarı (İlk 5 karakter): {YELP_API_KEY[:5]}*****")

try:
    response = requests.get(YELP_REVIEWS_URL, headers=headers, timeout=10)
    response.raise_for_status() # HTTP hataları için istisna fırlatır

    yelp_data = response.json()

    print("\n--- Yelp API Yanıtı (JSON) ---")
    import json
    print(json.dumps(yelp_data, indent=2, ensure_ascii=False))

    # Yorumları ayrıştır ve yazdır
    if "reviews" in yelp_data:
        print("\n--- Çekilen Yorumlar ---")
        if not yelp_data["reviews"]:
            print("Bu restoran için yorum bulunamadı veya erişilemiyor.")
        for review in yelp_data["reviews"]:
            print(f"Yorum: {review.get('text', 'Yorum metni yok')}")
            print(f"Puan: {review.get('rating', 'Yok')}")
            print(f"Yazar: {review.get('user', {}).get('name', 'Bilinmiyor')}")
            print("-" * 20)
    else:
        print("Yorum verisi bulunamadı.")

except requests.exceptions.HTTPError as http_err:
    print(f"\n--- HTTP Hata ---")
    print(f"HTTP hatası oluştu: {http_err}")
    print(f"Durum Kodu: {response.status_code}")
    print(f"Yanıt Metni: {response.text}")
except requests.exceptions.ConnectionError as conn_err:
    print(f"\n--- Bağlantı Hatası ---")
    print(f"Bağlantı hatası oluştu: {conn_err}")
except requests.exceptions.Timeout as timeout_err:
    print(f"\n--- Zaman Aşımı Hatası ---")
    print(f"İstek zaman aşımına uğradı: {timeout_err}")
except requests.exceptions.RequestException as req_err:
    print(f"\n--- Genel İstek Hatası ---")
    print(f"Bilinmeyen bir hata oluştu: {req_err}")
except json.JSONDecodeError as json_err:
    print(f"\n--- JSON Çözümleme Hatası ---")
    print(f"Yanıt JSON olarak çözümlenemedi: {json_err}")
    print(f"Yanıtın ham metni: {response.text}")