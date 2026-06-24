import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# --- 1. MEMUAT DATASET ---
file_csv = 'wazuh_alerts.csv'

if not os.path.exists(file_csv):
    print(f"File '{file_csv}' tidak ditemukan!")
    exit()

print("Membaca data...")
df = pd.read_csv(file_csv)

# --- 2. LABELING BERBASIS KONTEKS KEAMANAN ---
# Alih-alih hanya memakai threshold rule.level secara mentah,
# kita mendefinisikan kriteria False Alarm secara mandiri berdasarkan
# KONTEKS KEAMANAN dari deskripsi log Wazuh.
#
# Filosofi: Hanya log yang benar-benar berkaitan dengan SERANGAN SIBER
# yang dilabeli sebagai Attack (1). Log operasional sistem (disk penuh,
# install package, login sukses) BUKAN serangan meskipun level-nya tinggi.

# Daftar pola deskripsi yang merupakan SERANGAN NYATA
attack_patterns = [
    "authentication failed",
    "non-existent user",
    "brute force",
    "Multiple failed logins",
    "missed the password more than one time",
]

# Daftar pola deskripsi yang merupakan OPERASIONAL NORMAL (bukan serangan)
normal_patterns = [
    "File system full",
    "Partition usage reached",
    "dpkg",
    "Dpkg",
    "rootcheck",
    "PAM: Login session opened",
    "PAM: Login session closed",
    "authentication success",
    "Wazuh server started",
    "sudo",
    "New group added",
    "New user added",
    "connection reset",
]

def label_log(row):
    desc = str(row['rule.description'])
    # Cek apakah deskripsi cocok dengan pola serangan
    for pattern in attack_patterns:
        if pattern.lower() in desc.lower():
            return 1  # Serangan Nyata (True Positive)
    # Jika tidak cocok dengan pola serangan, maka Normal
    return 0  # Aktivitas Normal / False Positive

df['is_attack'] = df.apply(label_log, axis=1)

# Menghapus baris yang kosong (NaN) pada deskripsi peringatan
df = df.dropna(subset=['rule.description'])

X_text = df['rule.description']
y = df['is_attack']

print(f"\nTotal Data: {len(df)} baris")
print(f"Total Serangan (1): {len(df[df['is_attack'] == 1])}")
print(f"Total Normal   (0): {len(df[df['is_attack'] == 0])}")

# --- Tampilkan detail labeling per level untuk verifikasi ---
print("\n=== VERIFIKASI LABELING ===")
for level in sorted(df['rule.level'].unique()):
    subset = df[df['rule.level'] == level]
    descs = subset['rule.description'].unique()
    for d in descs:
        label = subset[subset['rule.description'] == d]['is_attack'].iloc[0]
        count = len(subset[subset['rule.description'] == d])
        status = "SERANGAN" if label == 1 else "NORMAL"
        print(f"  Level {level:2d} | {status:9s} | {count:4d}x | {d}")

# --- 3. EKSTRAKSI FITUR (Teks ke Angka) ---
print("\nMengubah teks log menjadi vektor TF-IDF...")
vectorizer = TfidfVectorizer()
X_vektor = vectorizer.fit_transform(X_text)

# Membagi data menjadi 80% untuk belajar, 20% untuk ujian (testing)
X_train, X_test, y_train, y_test = train_test_split(X_vektor, y, test_size=0.2, random_state=42)

# --- 4. MELATIH MODEL (Machine Learning) ---
print("Melatih Model Random Forest...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# --- 5. EVALUASI MODEL ---
y_pred = model.predict(X_test)
akurasi = accuracy_score(y_test, y_pred)

print("\n" + "="*50)
print("HASIL EVALUASI MODEL AI".center(50))
print("="*50)
print(f"Akurasi Model: {akurasi * 100:.2f}%")
print("\nDetail Laporan (Precision, Recall, F1-Score):")
print(classification_report(y_test, y_pred, target_names=["Normal/False Positive", "Serangan/True Positive"]))

# --- 6. MENYIMPAN MODEL ---
joblib.dump(model, 'ai_soc_model.pkl')
joblib.dump(vectorizer, 'vectorizer.pkl')

print("Model berhasil disimpan sebagai 'ai_soc_model.pkl' dan 'vectorizer.pkl'")
