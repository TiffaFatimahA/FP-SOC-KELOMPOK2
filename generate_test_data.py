import paramiko
import requests
import time
import subprocess

target_ip = "70.153.19.146"
username = "admin_soc"
password = "ProyekSoc2026!"

print("🚀 Memulai simulasi serangan untuk pengujian Wazuh + AI SOC...")

# ============================================================
# 1. Simulasi DDoS (SYN Flood menggunakan hping3)
# ============================================================
print("\n[1/4] Memicu peringatan DDoS (SYN Flood via hping3)...")
print("  Mengirim 500 paket SYN ke port 80 server korban...")
try:
    # hping3 mengirim paket SYN secara cepat (bukan --flood agar server tidak mati)
    # -S = SYN flag, -p 80 = port 80, -c 500 = kirim 500 paket, --faster = kecepatan tinggi
    result = subprocess.run(
        ["hping3", "-S", "-p", "80", "-c", "500", "--faster", target_ip],
        capture_output=True, text=True, timeout=15
    )
    print("  ✔️ SYN Flood (500 paket) berhasil dikirim ke server korban.")
    print("  Wazuh akan mendeteksi ini sebagai anomali koneksi/firewall.")
except FileNotFoundError:
    print("  ⚠️ hping3 tidak ditemukan. Install dengan: sudo apt install hping3")
    print("  Atau jalankan manual: hping3 -S -p 80 -c 500 --faster " + target_ip)
except subprocess.TimeoutExpired:
    print("  ✔️ SYN Flood dikirim (timeout tercapai, ini normal).")
except Exception as e:
    print(f"  ❌ Error: {e}")

time.sleep(2)

# ============================================================
# 2. Simulasi Malware (Mengunduh file EICAR)
# ============================================================
print("\n[2/4] Memicu peringatan Malware (EICAR Test File)...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(target_ip, port=22, username=username, password=password)
    client.exec_command("rm -f eicar.com.txt && wget -q -O eicar.com.txt https://secure.eicar.org/eicar.com.txt")
    print("  ✔️ File EICAR berhasil diunduh ke server korban.")
    print("  Wazuh akan mendeteksi perubahan file (File Integrity Monitoring).")
    time.sleep(2)
except Exception as e:
    print(f"  ❌ Gagal koneksi SSH: {e}")
finally:
    client.close()

# ============================================================
# 3. Simulasi Brute Force / Social Engineering (Failed Login)
# ============================================================
print("\n[3/4] Memicu peringatan Brute Force (SSH Login Gagal Berulang)...")
for i in range(5):
    try:
        dummy_client = paramiko.SSHClient()
        dummy_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        dummy_client.connect(target_ip, port=22, username="hacker_palsu", password="PasswordSalah123!", timeout=3)
    except paramiko.AuthenticationException:
        print(f"  ✔️ Percobaan login gagal ke-{i+1} berhasil dikirim.")
    except Exception:
        pass
    time.sleep(0.5)

# ============================================================
# 4. Simulasi Aktivitas Normal (False Alarm / Noise)
# ============================================================
print("\n[4/4] Menghasilkan aktivitas traffic web normal (False Alarm)...")
for i in range(3):
    try:
        requests.get(f"http://{target_ip}/", timeout=2)
        print(f"  ✔️ Ping HTTP ke-{i+1} terkirim (aktivitas normal).")
    except:
        print(f"  ➖ Server web belum aktif, ping dilewati.")
    time.sleep(0.5)

print("\n" + "="*60)
print("✅ SEMUA SIMULASI SELESAI!".center(60))
print("="*60)
print("\nRingkasan serangan yang dikirim:")
print("  • DDoS      : 500 paket SYN Flood via hping3")
print("  • Malware   : EICAR test file download")
print("  • Brute Force: 5x percobaan login SSH gagal")
print("  • Normal    : 3x HTTP ping (untuk uji False Positive)")
print("\nTunggu 1-2 menit, lalu cek Dasbor Wazuh untuk melihat hasilnya.")
