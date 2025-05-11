from flask import Blueprint, request, jsonify
from app.database import db_session
from app.models.user import User
from app.models.translation import Translation
from app.models.review import Review
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('routes', __name__)

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

@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Missing fields"}), 400

    user = db_session.query(User).filter_by(email=data["email"]).first()
    if not user or not check_password_hash(user.password, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful", "user_id": user.id}), 200

@bp.route("/translations", methods=["POST"])
def add_translation():
    data = request.get_json()
    if not data or not all(k in data for k in ("user_id", "original_text", "target_language")):
        return jsonify({"error": "Missing fields"}), 400

    new_translation = Translation(
        user_id=data["user_id"],
        original_text=data["original_text"],
        target_language=data["target_language"]
    )

    db_session.add(new_translation)
    db_session.commit()

    return jsonify({"message": "Translation added successfully"}), 201

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
