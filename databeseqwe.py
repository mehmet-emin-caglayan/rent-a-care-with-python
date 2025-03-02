import psycopg2
import pandas as pd

# PostgreSQL Bağlantı Bilgileri
DB_CONFIG = {
    "dbname": "modbus_db",
    "user": "postgres",
    "password": "mehmet125",  # PostgreSQL şifreni buraya gir!
    "host": "localhost",
    "port": "5433"
}


# PostgreSQL bağlantısını oluştur
def connect_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print("Veritabanına bağlanırken hata oluştu:", e)
        return None


# Veritabanından cihazları getir
def get_devices():
    conn = connect_db()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, device_name, ip_address, port, register_address, register_count, slave_address FROM modbus_devices")
    devices = cursor.fetchall()

    cursor.close()
    conn.close()
    return devices


def get_devices_web():
    """ Veritabanındaki cihazları çeker """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT id, device_name FROM modbus_devices ORDER BY id")
    devices = cursor.fetchall()
    conn.close()
    return [{"label": name, "value": device_id} for device_id, name in devices]


def get_parameters(device_id):
    """ Belirli bir cihazın modbus parametrelerini çeker """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT parameter_name FROM modbus_parameters WHERE device_id = %s", (device_id,))
    parameters = [row[0] for row in cursor.fetchall()]
    conn.close()
    return parameters


# Modbus verilerini veritabanına kaydet
def save_modbus_data(device_id, parameter_name, register_value):
    conn = connect_db()
    if not conn:
        return

    cursor = conn.cursor()

    # modbus_data tablosuna veri ekleyelim
    cursor.execute(
        "INSERT INTO modbus_data (device_id, parameter_name, register_value) VALUES (%s, %s, %s)",
        (device_id, parameter_name, register_value)
    )

    # Aynı zamanda modbus_parameters tablosunu güncelleyelim
    save_modbus_parameter_data(device_id, parameter_name, register_value)

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Cihaz {device_id}: {parameter_name} = {register_value} kaydedildi ve parametre değeri güncellendi.")


def save_modbus_parameter_data(device_id, parameter_name, register_value):
    """ Modbus parametre verilerini modbus_parameters tablosuna kaydeder veya günceller """
    conn = connect_db()
    if not conn:
        return

    cursor = conn.cursor()

    # Önce parametre zaten var mı kontrol et
    cursor.execute(
        "SELECT id FROM modbus_parameters WHERE device_id = %s AND parameter_name = %s",
        (device_id, parameter_name)
    )
    result = cursor.fetchone()

    if result:
        # Parametre varsa, değeri güncelle
        cursor.execute(
            "UPDATE modbus_parameters SET value = %s WHERE id = %s",
            (register_value, result[0])
        )
        print(f"✅ {parameter_name} parametre değeri güncellendi.")
    else:
        # Parametre yoksa, yeni ekle
        cursor.execute(
            "INSERT INTO modbus_parameters (device_id, parameter_name, value) VALUES (%s, %s, %s)",
            (device_id, parameter_name, register_value)
        )
        print(f"✅ {parameter_name} parametre değeri kaydedildi.")

    conn.commit()
    cursor.close()
    conn.close()


def get_modbus_parameters(device_id):
    """ Cihazın modbus parametrelerini ve değerlerini çeker """
    conn = connect_db()
    if not conn:
        return {}

    cursor = conn.cursor()
    cursor.execute(
        "SELECT parameter_name, register_index, scale_factor, offsett, value FROM modbus_parameters WHERE device_id = %s",
        (device_id,)
    )

    parameters = {}
    for row in cursor.fetchall():
        param_name, reg_index, scale, offset, value = row
        parameters[param_name] = {
            "index": reg_index,
            "carp": scale,
            "topla": offset,
            "value": value  # Parametre değerini ekliyoruz
        }

    cursor.close()
    conn.close()

    return parameters


def get_modbus_data(device_id):
    """ Belirli bir cihazın en son 100 ölçümünü çeker """
    conn = psycopg2.connect(**DB_CONFIG)
    query = """
        SELECT timestamp, parameter_name, register_value 
        FROM modbus_data 
        WHERE device_id = %s
        ORDER BY timestamp DESC
        LIMIT 100;
    """
    df = pd.read_sql(query, conn, params=(device_id,))
    conn.close()
    return df


def add_device(name, ip, port):
    """ Yeni bir cihaz ekler. """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO modbus_devices (device_name, ip_address, port) VALUES (%s, %s, %s)",
                   (name, ip, port))
    conn.commit()
    conn.close()


def update_device(device_id, name, ip, port):
    """ Mevcut cihazı günceller. """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("UPDATE modbus_devices SET device_name = %s, ip_address = %s, port = %s WHERE id = %s",
                   (name, ip, port, device_id))
    conn.commit()
    conn.close()


def delete_device(device_id):
    """ Bir cihazı siler. """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM modbus_devices WHERE id = %s", (device_id,))
    conn.commit()
    conn.close()
