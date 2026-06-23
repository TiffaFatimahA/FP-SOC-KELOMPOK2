import paramiko
import json
import pandas as pd
import sys

# ============================================================
# KONFIGURASI - Ganti dengan kredensial server Anda
# ============================================================
hostname = "YOUR_WAZUH_MANAGER_IP"
port = 22
username = "YOUR_SSH_USERNAME"
password = "YOUR_SSH_PASSWORD"

# File output lokal
output_csv = "wazuh_alerts.csv"

# Jumlah baris log terakhir yang ingin diambil
max_alerts = 5000

print(f"Mencoba terhubung ke Wazuh Manager ({hostname})...")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(hostname, port, username, password)
    print("Koneksi SSH berhasil! Mengunduh log...")

    # Perintah untuk membaca N baris terakhir dari alerts.json menggunakan sudo
    command = f"echo '{password}' | sudo -S tail -n {max_alerts} /var/ossec/logs/alerts/2026/Jun/ossec-alerts-22.json"
    stdin, stdout, stderr = client.exec_command(command)
    
    raw_output = stdout.read().decode('utf-8', errors='ignore')
    err_output = stderr.read().decode('utf-8', errors='ignore')

    if not raw_output.strip():
        print("Gagal mengambil data atau log masih kosong.")
        if err_output:
            print(f"Detail Error: {err_output}")
        sys.exit(1)

    print("Data berhasil diunduh. Memulai parsing JSON ke format CSV...")
    
    # Parsing baris demi baris JSON
    alerts_list = []
    for line in raw_output.strip().split('\n'):
        if not line.strip():
            continue
        try:
            alert_json = json.loads(line)
            
            # Ekstraksi field penting untuk dataset AI
            flat_alert = {
                "timestamp": alert_json.get("timestamp", ""),
                "agent.name": alert_json.get("agent", {}).get("name", "Wazuh-Manager-Server"),
                "rule.description": alert_json.get("rule", {}).get("description", ""),
                "rule.level": alert_json.get("rule", {}).get("level", 0),
                "rule.id": alert_json.get("rule", {}).get("id", ""),
                # full_log bisa berguna untuk analisis teks lebih mendalam
                "full_log": alert_json.get("full_log", "").replace('\n', ' ')
            }
            alerts_list.append(flat_alert)
        except json.JSONDecodeError:
            continue  # Lewati baris jika format JSON tidak valid

    if not alerts_list:
        print("Tidak ada alert valid yang berhasil di-parse.")
        sys.exit(1)

    # Convert ke DataFrame Pandas dan simpan ke CSV
    df = pd.DataFrame(alerts_list)
    df.to_csv(output_csv, index=False)
    
    print(f"\n🎉 Berhasil mengumpulkan data!")
    print(f"File disimpan di: {output_csv}")
    print(f"Total baris log terkumpul: {len(df)}")
    print("\nContoh 5 baris data teratas:")
    print(df[["timestamp", "rule.description", "rule.level"]].head())

except Exception as e:
    print(f"Terjadi kesalahan: {e}")
finally:
    client.close()
    print("\nKoneksi SSH ditutup.")
