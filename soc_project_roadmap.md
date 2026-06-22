# 🗺️ Roadmap & Detail Teknis: Human-AI Collaboration SOC

Dokumen ini adalah panduan langkah demi langkah yang **sangat mendetail** untuk menyelesaikan proyek akhir Anda. Silakan bagikan dokumen ini kepada masing-masing penanggung jawab divisi.

---

## 📅 Fase 1: Persiapan & Infrastruktur (Selesai!) ✅
*(Sudah dikerjakan oleh Tim Cloud)*
- [x] **Wazuh Manager (Server Utama):** Berjalan di `20.204.12.205`
- [x] **Wazuh Agent (Server Korban):** Berjalan di `70.153.19.146`

### 🔐 Informasi Login Server (SSH)
Kedua server Azure (Manager maupun Korban) menggunakan informasi *login* yang sama:
- **Username SSH:** `admin_soc`
- **Password SSH:** `ProyekSoc2026!`

**Cara Login (Gunakan Terminal / WSL / Command Prompt):**
- Untuk masuk ke Server Utama (Wazuh): ketik `ssh admin_soc@20.204.12.205`
- Untuk masuk ke Server Korban: ketik `ssh admin_soc@70.153.19.146`
*(Saat memasukkan password, teksnya memang **tidak akan muncul** di layar. Ketik saja terus lalu tekan Enter).*

### 🔐 Informasi Login Dasbor Wazuh
Untuk mengekspor data log dan hasil deteksi, buka browser dan masuk ke dasbor web:
- **URL Dasbor:** `https://20.204.12.205` *(Klik Advanced -> Proceed to unsafe jika ada peringatan SSL)*
- **Username:** `admin`
- **Password:** `ProyekSoc2026-`

---

## 📅 Fase 2: Skenario Serangan & Pengumpulan Data
*(Ditugaskan kepada: Tim Red Team)*

Tugas Anda adalah membuat Wazuh "berteriak" dengan cara menyerang server korban.

### 1. Simulasi Serangan DDoS
Gunakan OS Kali Linux atau WSL, buka terminal dan jalankan perintah `hping3` untuk membanjiri server korban dengan paket SYN:
```bash
# Perintah ini mengirim paket tanpa henti (flood) ke port 80 server korban
sudo hping3 -S -p 80 --flood 70.153.19.146
```
*Biarkan berjalan selama 5-10 menit, lalu tekan `Ctrl+C` untuk mematikan.*

### 2. Simulasi Malware (EICAR Test)
*Login* ke dalam server korban menggunakan SSH (`ssh admin_soc@70.153.19.146`), lalu *download* file pancingan malware internasional (EICAR):
```bash
wget https://secure.eicar.org/eicar.com.txt
```
*Wazuh File Integrity Monitoring (FIM) dan pendeteksi ancaman akan langsung mencatat masuknya file berbahaya ini.*

### 3. Simulasi Brute Force SSH (Social Engineering)
Buka terminal dari komputer mana saja, cobalah login ke server korban dengan *password* yang salah berkali-kali secara sengaja:
```bash
ssh admin_soc@70.153.19.146
# Masukkan password ngawur 5-10 kali sampai koneksi ditutup.
```

### 4. Ekspor Data Log (Untuk Tim AI)
Setelah puas menyerang, masuk ke **Dasbor Wazuh** (`https://20.204.12.205`).
- Masuk ke menu **Modules** -> **Security Events**.
- Filter waktu di pojok kanan atas ke **Last 24 Hours**.
- Klik tombol **Save / Export** (biasanya berupa ikon disket atau panah ke bawah di pojok kanan atas tabel) untuk mengunduh log sebagai format `.csv` atau `.json`.
- Berikan file ini ke Tim AI!

---

## 📅 Fase 3: Pembuatan Model AI Lokal
*(Ditugaskan kepada: Tim Data/AI Engineer)*

Anda menerima file data `.csv` atau `.json` dari Red Team. Data ini campur aduk antara *False Alarm* (aktivitas biasa) dan *Serangan Asli* (DDoS/Malware tadi).

### Langkah Teknis:
1. **Preprocessing (Pembersihan Data):**
   Gunakan Python (`pandas`). Ambil kolom yang penting saja, seperti `rule.description`, `agent.ip`, atau `full_log`.
2. **Pelabelan (Labeling):**
   Buat kolom baru bernama `is_attack`. 
   - Beri nilai `1` untuk log yang Anda tahu itu serangan asli (misal log dari hping3).
   - Beri nilai `0` untuk peringatan yang ternyata cuma aktivitas normal.
3. **Training Model:**
   Gunakan algoritma **Random Forest**. Ini adalah contoh kerangka kodenya:
   ```python
   from sklearn.feature_extraction.text import TfidfVectorizer
   from sklearn.ensemble import RandomForestClassifier
   import joblib

   # 1. Ubah teks log menjadi angka (TF-IDF)
   vectorizer = TfidfVectorizer()
   X = vectorizer.fit_transform(data['rule_description'])
   y = data['is_attack']

   # 2. Latih Model
   model = RandomForestClassifier()
   model.fit(X, y)

   # 3. Simpan Model agar bisa dipakai nanti
   joblib.dump(model, 'ai_soc_model.pkl')
   joblib.dump(vectorizer, 'vectorizer.pkl')
   ```

---

## 📅 Fase 4: Integrasi Wazuh, AI, dan SOAR
*(Ditugaskan kepada: Tim SOAR & Cloud)*

AI sudah pintar dan bisa membedakan serangan. Sekarang kita pasang AI ini sebagai "Satpam Pintar" di server.

### 1. Buat API AI Lokal (Flask)
Di server Wazuh Manager (`20.204.12.205`), buat file Python `api_ai.py`:
```python
from flask import Flask, request
import joblib

app = Flask(__name__)
model = joblib.load('ai_soc_model.pkl')
vectorizer = joblib.load('vectorizer.pkl')

@app.route('/cek_log', methods=['POST'])
def cek_log():
    log_wazuh = request.json['deskripsi_log']
    vektor = vectorizer.transform([log_wazuh])
    prediksi = model.predict(vektor)
    
    if prediksi[0] == 1:
        # SERANGAN ASLI -> Teruskan ke SOAR (Shuffle / n8n)
        return "True Positive"
    else:
        # FALSE ALARM -> Buang log-nya
        return "False Positive"

if __name__ == '__main__':
    app.run(port=5000)
```

### 2. Hubungkan Wazuh ke Flask API
Buka file konfigurasi Wazuh (`/var/ossec/etc/ossec.conf`) dan tambahkan blok *integration*:
```xml
<integration>
  <name>custom-ai</name>
  <hook_url>http://127.0.0.1:5000/cek_log</hook_url>
  <alert_format>json</alert_format>
</integration>
```
*Restart* Wazuh: `sudo systemctl restart wazuh-manager`.

### 3. Otomatisasi SOAR
- Buka platform SOAR Anda (misal: *Shuffle* atau *Wazuh Active Response*).
- Buat *playbook*: "Jika menerima notifikasi True Positive dari AI, jalankan perintah SSH ke Server Korban (`70.153.19.146`) untuk memblokir IP penyerang menggunakan *iptables*".

---

## 📅 Fase 5: Penulisan Laporan Akhir

- **Bab Arsitektur:** Masukkan gambar topologi server Azure.
- **Bab Metodologi AI:** Jelaskan kenapa memilih Random Forest, tunjukkan nilai akurasinya (F1-Score).
- **Bab Evaluasi:** Buktikan bahwa tanpa AI, Wazuh menghasilkan X peringatan. Dengan AI, peringatan turun menjadi Y (False alarm berkurang), tapi serangan asli tetap terblokir oleh SOAR.
