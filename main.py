import app.firebase_admin_init  # Firebase Admin başlatılır
from flask import Flask
from flask_cors import CORS
from app.routes import bp
from app.database import Base, engine

def create_app():
    app = Flask(__name__)
    
    # CORS ayarları: frontend'in portunu burada açıkça belirtebilirsin (güvenlik için önerilir)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Veritabanı tablolarını oluştur
    with app.app_context():
        Base.metadata.create_all(bind=engine)

    # Blueprint'i yükle
    app.register_blueprint(bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
