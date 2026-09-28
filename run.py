from dotenv import load_dotenv

load_dotenv()  # carga variables desde .env en desarrollo local

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False), host="0.0.0.0", port=5000)
