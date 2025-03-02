import time
import threading
import login_api  # Flask login API'sini import ediyoruz
from device_live_api import app  # device_live_api.py'deki Flask uygulamasını import ediyoruz
from databeseqwe import get_devices, save_modbus_data
from modbus_client import read_modbus
from process_data import process_modbus_data

# Flask'i farklı bir thread'de çalıştır
def start_flask():
    login_api.app.run(debug=True, use_reloader=False)  # login_api'nin Flask uygulamasını 5001 portunda başlatıyoruz


def start_device_live_api():
    app.run(debug=True, port=5002, use_reloader=False)  # device_live_api'nin Flask uygulamasını 5002 portunda başlatıyoruz

def main():
    while True:
        devices = get_devices()  # Cihazları veritabanından al

        for device in devices:
            device_id, device_name, ip, port, reg_addr, reg_count, slav_adres = device

            print(f"{device_name} ({ip}:{port}) için Modbus verisi okunuyor...")

            modbus_data = read_modbus(ip, port, reg_addr, reg_count, slav_adres)  # Modbus verilerini al

            if modbus_data:
                processed_data = process_modbus_data(device_id, modbus_data)  # Veriyi işle

                for param, value in processed_data.items():
                    save_modbus_data(device_id, param, value)  # Veriyi veritabanına kaydet
            else:
                print(f"❌ {device_name} için veri okunamadı!")

        print("\n📌 **Bir sonraki okuma turuna geçiliyor...**")
        time.sleep(5)  # **5 saniye bekleyerek tekrar oku**

# Flask uygulamalarını ve modbus işlemlerini aynı anda çalıştır
if __name__ == "__main__":
    # Flask'ı iki ayrı thread içinde çalıştırıyoruz.
    login_api_thread = threading.Thread(target=start_flask)  # Login API thread
    device_live_api_thread = threading.Thread(target=start_device_live_api)  # Device Live API thread

    login_api_thread.start()
    device_live_api_thread.start()

    main()
