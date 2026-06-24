import paramiko
import json
import time

# ============================================================
# KONFIGURASI - Ganti dengan kredensial server Anda
# ============================================================
host = 'YOUR_WAZUH_MANAGER_IP'
username = 'YOUR_SSH_USERNAME'
password = 'YOUR_SSH_PASSWORD'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=22, username=username, password=password)

print("="*70)
print("DEMO PENGUJIAN OTOMATIS: KECERDASAN AI SOC".center(70))
print("="*70)

test_cases = [
    {
        "title": "Log Operasional Sistem (Bukan Serangan)",
        "desc":  "Karyawan berhasil login SSH dengan password yang benar.",
        "log":   {"rule": {"description": "sshd: authentication success."}},
        "expected": "False Positive (Normal/Aman)"
    },
    {
        "title": "Log Disk Penuh (Bukan Serangan)",
        "desc":  "Server melaporkan penyimpanan penuh. Ini masalah infrastruktur, BUKAN serangan hacker.",
        "log":   {"rule": {"description": "File system full."}},
        "expected": "False Positive (Normal/Aman)"
    },
    {
        "title": "Log Install Software (Bukan Serangan)",
        "desc":  "Admin menginstall software baru di server. Ini operasi rutin.",
        "log":   {"rule": {"description": "New dpkg (Debian Package) installed."}},
        "expected": "False Positive (Normal/Aman)"
    },
    {
        "title": "Log Serangan Brute Force (SERANGAN NYATA!)",
        "desc":  "Hacker jahat mencoba menebak password ribuan kali secara otomatis.",
        "log":   {"rule": {"description": "sshd: brute force trying to get access to the system. Authentication failed."}},
        "expected": "True Positive (Serangan Nyata)"
    },
    {
        "title": "Log Login Gagal Berulang (SERANGAN NYATA!)",
        "desc":  "Terdeteksi banyak percobaan login gagal dalam waktu singkat.",
        "log":   {"rule": {"description": "PAM: Multiple failed logins in a small period of time."}},
        "expected": "True Positive (Serangan Nyata)"
    },
]

for i, case in enumerate(test_cases, 1):
    print(f"\n{'='*70}")
    print(f"[SKENARIO {i}] {case['title']}")
    print(f"Konteks: {case['desc']}")
    print(f"Log yang dikirim ke AI: '{case['log']['rule']['description']}'")

    cmd = f"curl -s -X POST http://127.0.0.1:5000/cek_log -H 'Content-Type: application/json' -d '{json.dumps(case['log'])}'"
    stdin, stdout, stderr = client.exec_command(cmd)
    result = stdout.read().decode().strip()

    time.sleep(1)
    try:
        res = json.loads(result)
        status = res.get("status")
        print(f"Keputusan AI           : >> {status} <<")
        print(f"Yang Diharapkan        : {case['expected']}")

        if status == "True Positive":
            print("Tindakan SOAR          : EKSEKUSI firewall-drop (IP DIBLOKIR!)")
        else:
            print("Tindakan SOAR          : DIABAIKAN (Tidak ada pemblokiran)")
    except:
        print(f"Hasil Mentah: {result}")

print(f"\n{'='*70}")
print("DEMO SELESAI".center(70))
print("="*70)

client.close()
