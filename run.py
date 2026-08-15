import os
from dotenv import load_dotenv

# Load .env before everything else
load_dotenv()

from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))   # 8080 avoids macOS AirPlay / Windows Hyper-V conflicts
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", True))
