from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Oturum yönetimi için gerekli
CORS(app, supports_credentials=True)  # CORS desteği

# PostgreSQL bağlantı bilgileri
DB_CONFIG = {
    "dbname": "modbus_db",
    "user": "postgres",
    "password": "mehmet125",
    "host": "localhost",
    "port": "5433"
}

def check_user_credentials(username, password):
    """ Kullanıcı adı ve şifreyi veritabanından kontrol eder """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        return user and user[0] == password
    except Exception as e:
        print(f"❌ Veritabanı hatası: {e}")
        return False

@app.route('/')
def home():
    """ Login sayfasını göster """
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """ Kullanıcı girişini kontrol eden API """
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if check_user_credentials(username, password):
        session["username"] = username  # Oturum başlat
        return jsonify({"message": "Giriş başarılı", "redirect": url_for("dashboard")}), 200
    return jsonify({"message": "Hatalı kullanıcı adı veya şifre"}), 401

@app.route('/dashboard')
def dashboard():
    """ Dashboard ekranı (Kullanıcı giriş yapmışsa açılır) """
    if "username" in session:
        return render_template("dashboard.html", username=session["username"])
    return redirect(url_for("home"))  # Giriş yapılmamışsa login sayfasına yönlendir

@app.route('/live_value')
def live_value():
    return render_template('live_value.html')

@app.route('/logout')
def logout():
    """ Kullanıcıyı çıkış yaptır """
    session.pop("username", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
