from flask import Flask, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app, supports_credentials=True)  # CORS desteği ve oturum paylaşımı

# PostgreSQL bağlantı bilgileri
DB_CONFIG = {
    "dbname": "modbus_db",
    "user": "postgres",
    "password": "mehmet125",
    "host": "localhost",
    "port": "5433"
}

# SQLAlchemy bağlantı dizesi
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "supersecretkey"  # Oturum yönetimi için gerekli

db = SQLAlchemy()
db.init_app(app)


# **Modbus Devices Modeli**
class ModbusDevice(db.Model):
    __tablename__ = "modbus_devices"
    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(50), nullable=False)
    ip_address = db.Column(db.String(15), nullable=False)
    port = db.Column(db.Integer, nullable=False, default=502)
    register_address = db.Column(db.Integer, nullable=False)
    register_count = db.Column(db.Integer, nullable=False)
    slave_address = db.Column(db.Integer, nullable=False, default=1)

    parameters = db.relationship("ModbusDeviceParameter", back_populates="device")
    user_tables = db.relationship("UserTable", back_populates="device")


# **ModbusDeviceParameter Modeli**
class ModbusDeviceParameter(db.Model):
    __tablename__ = "modbus_parameters"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("modbus_devices.id"), nullable=False)
    parameter_name = db.Column(db.String(50), nullable=False)
    register_index = db.Column(db.Integer, nullable=False)
    scale_factor = db.Column(db.Float, default=1)
    offsett = db.Column(db.Float, default=0)
    value = db.Column(db.Integer)

    device = db.relationship("ModbusDevice", back_populates="parameters")


# **UserTable Modeli**
class UserTable(db.Model):
    __tablename__ = "user_tables"
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(100), nullable=False, unique=True)
    device_id = db.Column(db.Integer, db.ForeignKey("modbus_devices.id"), nullable=False)
    parameters = db.Column(db.JSON, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)  # Kullanıcı kimliği eklendi

    device = db.relationship("ModbusDevice", back_populates="user_tables")


# **Kullanıcı Tablosunu Kaydetme**
@app.route("/api/user_table", methods=["POST"])
def save_user_table():
    try:
        if "user_id" not in session:
            return jsonify({"error": "Kullanıcı oturumu bulunamadı!"}), 401

        data = request.json
        table_name = data.get("table_name")
        device_id = data.get("device_id")
        parameters = data.get("parameters")
        user_id = session["user_id"]  # Oturumdan user_id al

        if not table_name or not device_id or not parameters:
            return jsonify({"error": "Eksik veri gönderildi!"}), 400

        new_table = UserTable(
            table_name=table_name,
            device_id=device_id,
            parameters=parameters,
            user_id=user_id
        )
        db.session.add(new_table)
        db.session.commit()

        return jsonify({"message": "Tablo başarıyla kaydedildi!", "table_id": new_table.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Veritabanı hatası: {str(e)}"}), 500


# **Kullanıcının Kayıtlı Tablolarını Getirme**
@app.route("/api/user_tables", methods=["GET"])
def get_user_tables():
    try:
        if "user_id" not in session:
            return jsonify({"error": "Kullanıcı oturumu bulunamadı!"}), 401

        user_id = session["user_id"]  # Oturumdan user_id al
        tables = UserTable.query.filter_by(user_id=user_id).all()
        table_list = [{
            "id": table.id,
            "table_name": table.table_name,
            "device_id": table.device_id,
            "parameters": table.parameters
        } for table in tables]

        return jsonify(table_list)

    except Exception as e:
        return jsonify({"error": f"Veritabanı hatası: {str(e)}"}), 500


# **Tüm Cihazları Getirme**
@app.route("/api/devices", methods=["GET"])
def get_devices():
    try:
        devices = ModbusDevice.query.all()
        device_list = [{
            "id": device.id,
            "device_name": device.device_name,
            "ip_address": device.ip_address,
            "port": device.port,
            "slave_address": device.slave_address
        } for device in devices]

        return jsonify(device_list)

    except Exception as e:
        return jsonify({"error": f"Veritabanı hatası: {str(e)}"}), 500


# **Belirli Bir Cihazın Parametrelerini Getirme**
@app.route("/api/device/<int:device_id>/parameters", methods=["GET"])
def get_device_parameters(device_id):
    try:
        device = ModbusDevice.query.filter_by(id=device_id).first()

        if device:
            parameters = [{
                "id": param.id,
                "parameter_name": param.parameter_name,
                "register_index": param.register_index,
                "scale_factor": param.scale_factor,
                "offsett": param.offsett
            } for param in device.parameters]

            return jsonify(parameters)
        else:
            return jsonify({"error": "Cihaz bulunamadı!"}), 404

    except Exception as e:
        return jsonify({"error": f"Veritabanı hatası: {str(e)}"}), 500


# **Belirli Bir Cihazın Bir Parametresinin Son Değerini Getirme**
@app.route("/api/device/<int:device_id>/parameter/<string:parameter_name>/latest", methods=["GET"])
def get_device_parameter_latest(device_id, parameter_name):
    try:
        device = ModbusDevice.query.filter_by(id=device_id).first()
        if not device:
            return jsonify({"error": "Cihaz bulunamadı!"}), 404

        parameter = ModbusDeviceParameter.query.filter_by(device_id=device_id, parameter_name=parameter_name).first()
        if not parameter:
            return jsonify({"error": "Parametre bulunamadı!"}), 404

        latest_value = parameter.value
        if latest_value is None:
            return jsonify({"error": "En son veri bulunamadı!"}), 404

        response = {
            "device_name": device.device_name,
            "parameter_name": parameter.parameter_name,
            "register_value": latest_value,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Veritabanı hatası: {str(e)}"}), 500


if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            print("✅ Veritabanı bağlantısı başarılı!")
        except Exception as e:
            print(f"❌ Veritabanına bağlanırken hata oluştu: {str(e)}")

    app.run(debug=True, use_reloader=False, port=5002)
