import paramiko
import requests
import time

# ============================================================
# KONFIGURASI - Ganti dengan kredensial server Anda
# ============================================================
target_ip = "YOUR_WAZUH_AGENT_IP"
username = "YOUR_SSH_USERNAME"
password = "YOUR_SSH_PASSWORD"

print("🚀 Memulai simulasi pengumpulan data aman untuk Wazuh...")

# 1. Simulasi Malware (Mengunduh file EICAR)
# EICAR adalah file teks standar industri yang aman, tetapi akan dideteksi sebagai malware oleh semua sistem keamanan.
print("\n[1/3] Memicu peringatan File Integrity & Malware (EICAR)...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(target_ip, port=22, username=username, password=password)
    # Menghapus file lama jika ada, lalu mengunduh yang baru
    client.exec_command("rm -f eicar.com.txt && wget -q -O eicar.com.txt https://secure.eicar.org/eicar.com.txt")
    print("  ✔️ File EICAR berhasil diunduh ke server korban.")
    time.sleep(2)
except Exception as e:
    print(f"  ❌ Gagal koneksi SSH: {e}")
finally:
    client.close()

# 2. Simulasi Brute Force / Social Engineering (Failed Login)
print("\n[2/3] Memicu peringatan Kegagalan Autentikasi (Failed SSH Login)...")
for i in range(2):
    try:
        dummy_client = paramiko.SSHClient()
        dummy_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Sengaja menggunakan password yang salah untuk memicu log keamanan
        dummy_client.connect(target_ip, port=22, username="hacker_palsu", password="PasswordSalah123!", timeout=3)
    except paramiko.AuthenticationException:
        print(f"  ✔️ Percobaan login gagal ke-{i+1} berhasil dikirim.")
    except Exception:
        pass
    time.sleep(0.1)

# 3. Simulasi Aktivitas Normal (False Alarm)
print("\n[3/3] Menghasilkan aktivitas traffic web normal...")
for i in range(2):
    try:
        requests.get(f"http://{target_ip}/", timeout=2)
        print(f"  ✔️ Ping HTTP ke-{i+1} terkirim.")
    except:
        print(f"  ➖ Server web belum aktif, ping dilewati.")
    time.sleep(0.1)

print("\n✅ Simulasi Selesai!")
print("Silakan tunggu 1-2 menit agar Wazuh memproses log tersebut.")
print("Setelah itu, jalankan: python get_wazuh_alerts.py")
