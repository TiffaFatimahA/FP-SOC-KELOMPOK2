# 🛡️ Reducing SOC False Alarms through a Human-AI Collaboration Model

**Final Project - Security Operations Center (SOC) | Semester Genap 2024/2025**

## 📋 Deskripsi Proyek

Proyek ini membangun sistem **Human-AI Collaboration SOC** yang mengintegrasikan model Machine Learning ke dalam arsitektur Wazuh SIEM untuk mengurangi *false alarm* tanpa mengorbankan akurasi deteksi. Sistem secara otomatis mengklasifikasikan peringatan keamanan sebagai **True Positive** (serangan nyata) atau **False Positive** (alarm palsu), lalu merespons ancaman secara otomatis melalui mekanisme SOAR.

## 🏗️ Arsitektur Sistem

```
┌─────────────────┐     ┌──────────────────────────────────────────────┐
│   Attacker PC    │     │          Azure Cloud Infrastructure          │
│   (Kali Linux)   │     │                                              │
│                  │     │  ┌──────────────┐    ┌───────────────────┐   │
│  • DDoS (hping3) ├────►│  │ Wazuh Agent  │───►│  Wazuh Manager    │   │
│  • Malware       │     │  │ 70.153.19.146│    │  20.204.12.205    │   │
│  • Brute Force   │     │  └──────────────┘    │                   │   │
│                  │     │                      │  ┌─────────────┐  │   │
└──────────────────┘     │                      │  │ Flask AI API│  │   │
                         │                      │  │ (port 5000) │  │   │
                         │                      │  │             │  │   │
                         │                      │  │ Random      │  │   │
                         │                      │  │ Forest +    │  │   │
                         │                      │  │ TF-IDF      │  │   │
                         │                      │  └──────┬──────┘  │   │
                         │                      │         │         │   │
                         │                      │         ▼         │   │
                         │                      │  ┌─────────────┐  │   │
                         │                      │  │    SOAR      │  │   │
                         │                      │  │ Active Resp. │  │   │
                         │                      │  │ firewall-drop│  │   │
                         │                      │  └─────────────┘  │   │
                         │                      └───────────────────┘   │
                         └──────────────────────────────────────────────┘
```

### Alur Kerja Sistem:
1. **Serangan masuk** ke Wazuh Agent (server korban)
2. Wazuh Agent meneruskan log ke **Wazuh Manager**
3. Wazuh Manager mengirim alert ke **Flask AI API** melalui Custom Integration
4. Model AI (**Random Forest + TF-IDF**) menganalisis deskripsi log
5. Jika **True Positive** → SOAR memicu **Active Response (firewall-drop)** untuk memblokir IP penyerang secara otomatis
6. Jika **False Positive** → Alert diabaikan, mengurangi beban analis SOC

## 🎯 Skenario Serangan

| No | Jenis Serangan | Tools | Deskripsi |
|----|---------------|-------|-----------|
| 1 | **DDoS** | `hping3 --flood` | SYN Flood ke port 80 server korban |
| 2 | **Malware** | EICAR Test File | Download file standar industri untuk trigger deteksi malware |
| 3 | **Social Engineering** | SSH Brute Force | Percobaan login dengan kredensial palsu berulang kali |

## 🤖 Penjelasan Model AI

### Algoritma: Random Forest Classifier
- **Mengapa Random Forest?** Cocok untuk klasifikasi teks keamanan karena tahan terhadap overfitting dan mampu menangani fitur berdimensi tinggi dari TF-IDF.
- **Jumlah Trees:** 100 (n_estimators=100)

### Feature Engineering: TF-IDF Vectorizer
- Mengubah teks deskripsi log (`rule.description`) menjadi vektor numerik
- TF-IDF memberikan bobot lebih tinggi pada kata-kata unik yang membedakan serangan dari aktivitas normal

### Kriteria Labeling (False Alarm Definition)
- **Serangan (is_attack=1):** Log dengan `rule.level >= 5` (level keparahan menengah ke atas)
- **Normal (is_attack=0):** Log dengan `rule.level < 5` (aktivitas operasional biasa)
- Kriteria ini didefinisikan secara mandiri berdasarkan analisis distribusi data Wazuh

### Data Training
- **Sumber:** 3.457 baris log asli dari Wazuh Manager
- **Split:** 80% training, 20% testing
- **Format:** CSV dengan kolom timestamp, agent.name, rule.description, rule.level, rule.id, full_log

## 📊 Benchmark Metrics

| Metrik | Nilai |
|--------|-------|
| **Accuracy** | 100% |
| **Precision** | 1.00 |
| **Recall** | 1.00 |
| **F1-Score** | 1.00 |

> **Catatan:** Akurasi 100% tercapai karena distribusi teks antara kelas serangan dan normal sangat terpisah secara linguistik dalam dataset Wazuh. Pada implementasi dengan data yang lebih bervariasi, akurasi diharapkan lebih rendah namun tetap optimal.

## 📁 Struktur File

```
├── train_ai_model.py          # Script pelatihan model AI (TF-IDF + Random Forest)
├── get_wazuh_alerts.py         # Script ekstraksi log dari Wazuh Manager
├── generate_test_data.py       # Script simulasi serangan (DDoS, Malware, Brute Force)
├── deploy_integration.py       # Script deployment & integrasi AI ke Wazuh
├── wazuh_alerts.csv            # Dataset 3.457 baris log asli Wazuh
├── ai_soc_model.pkl            # Model Random Forest yang sudah dilatih
├── vectorizer.pkl              # TF-IDF Vectorizer yang sudah dilatih
└── README.md                   # Dokumentasi proyek
```

## 🚀 Cara Menjalankan

### Prerequisites
```bash
pip install paramiko pandas scikit-learn flask joblib requests
```

### 1. Ekstraksi Data dari Wazuh
```bash
python get_wazuh_alerts.py
```

### 2. Training Model AI
```bash
python train_ai_model.py
```

### 3. Deploy Integrasi ke Server
```bash
python deploy_integration.py
```

### 4. Menjalankan Simulasi Serangan
```bash
python generate_test_data.py
```

## 📈 Analisis Hasil

### Sebelum AI (Wazuh Default)
- Wazuh menghasilkan **ribuan peringatan** termasuk banyak false alarm
- Analis SOC harus meninjau setiap peringatan secara manual
- Risiko *alert fatigue* dan *burnout* tinggi

### Sesudah AI (Human-AI Collaboration)
- Model AI memfilter peringatan secara otomatis
- Hanya **True Positive** yang diteruskan ke SOAR untuk ditindaklanjuti
- **False Positive** diabaikan → beban kerja analis SOC berkurang drastis
- Active Response (`firewall-drop`) memblokir IP penyerang secara otomatis dalam hitungan milidetik

### Bukti SOAR Bekerja
- **Rule ID 100005 (Level 12):** AI mendeteksi serangan sebagai True Positive
- **Rule ID 651 (Level 3):** Active Response memblokir IP penyerang via firewall-drop
- Kedua rule muncul berurutan di Dashboard Wazuh, membuktikan alur otomatis End-to-End

## 🛠️ Tech Stack
- **SIEM:** Wazuh 4.9.2
- **Cloud:** Microsoft Azure (Free-tier Student)
- **AI/ML:** scikit-learn (Random Forest + TF-IDF)
- **API:** Flask (Python)
- **SOAR:** Wazuh Active Response (firewall-drop)
- **Attack Tools:** hping3, EICAR, Paramiko SSH

## 👥 Tim
Kelompok 2 - Final Project SOC Semester Genap 2024/2025
