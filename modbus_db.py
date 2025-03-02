import psycopg2
from pymodbus.client import ModbusTcpClient

# PostgreSQL Veritabanı Bağlantı Bilgileri
DB_CONFIG = {
    "dbname": "modbus_db",
    "user": "postgres",
    "password": "mehmet125",  # PostgreSQL şifreni buraya gir!
    "host": "localhost",
    "port": "5433"
}


# Veritabanından cihaz bilgilerini çek
def get_devices_from_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT id, device_name, ip_address, port, register_address, register_count FROM modbus_devices")
        devices = cursor.fetchall()  # Cihazları liste olarak al

        cursor.close()
        conn.close()
        return devices
    except Exception as e:
        print("Veritabanı hatası:", e)
        return []


# Okunan verileri PostgreSQL'e kaydet
def save_data_to_db(device_id, register_address, register_value):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO modbus_data (device_id, register_address, register_value) VALUES (%s, %s, %s)",
                       (device_id, register_address, str(register_value)))

        conn.commit()
        cursor.close()
        conn.close()
        print(f"Cihaz {device_id}: Veriler veritabanına kaydedildi.")
    except Exception as e:
        print("Veritabanına yazma hatası:", e)


# Modbus verilerini oku
def read_modbus_data():
    devices = get_devices_from_db()  # Cihaz bilgilerini çek

    for device in devices:
        device_id, device_name, ip, port, reg_addr, reg_count = device

        print(f"{device_name} ({ip}:{port}) cihazına bağlanılıyor...")

        client = ModbusTcpClient(ip, port=port)  # Modbus istemcisi oluştur

        if client.connect():
            print(f"{device_name}: Modbus bağlantısı başarılı!")
            adress = 1
            # Register değerlerini oku
            response = client.read_holding_registers(reg_addr, reg_count, adress)

            if not response.isError():
                print(f"{device_name} Verileri:", response.registers)
                save_data_to_db(device_id, reg_addr, response.registers)  # Veriyi DB'ye kaydet
            else:
                print(f"{device_name}: Modbus okuma hatası!")

            client.close()
        else:
            print(f"{device_name}: Modbus sunucusuna bağlanılamadı!")


# Ana program
if __name__ == "__main__":
    read_modbus_data()
