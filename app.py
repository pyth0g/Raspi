from flask import Flask
from views import views

app = Flask(__name__)
app.register_blueprint(views, url_prefix="/")

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=3000)