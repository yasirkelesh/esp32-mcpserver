# Basit test için
import requests

raspi_IP = "192.168.205.68"

def control_servo(angle):
    try:
        response = requests.post(f"http://{raspi_IP}/servo", data={"angle": angle})
        print(f"✅ Servo {angle} dereceye hareket etti!")
        return response.json()
    except Exception as e:
        print(f"❌ Hata: {e}")

# Test
if __name__ == "__main__":
    while True:
        angle = input("Servo açısı (0-180) veya 'q' çıkış: ")
        if angle == 'q':
            break
        try:
            control_servo(int(angle))
        except ValueError:
            print("Geçerli bir sayı girin!")