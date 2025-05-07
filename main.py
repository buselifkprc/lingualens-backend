from flask import Flask
from flask_cors import CORS
from app.routes import bp
from app.database import Base, engine

app = Flask(__name__)
CORS(app)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Register routes
app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(debug=True)
