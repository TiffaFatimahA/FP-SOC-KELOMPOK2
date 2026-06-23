import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# --- 1. MEMUAT DATASET ---
# Pastikan Anda meletakkan file CSV hasil export Wazuh di folder yang sama dengan script ini
file_csv = 'wazuh_alerts.csv' 

if not os.path.exists(file_csv):
    print(f"⚠️ File '{file_csv}' tidak ditemukan!")
    print("Silakan export log dari 'Security Events' di Dasbor Wazuh, lalu simpan dengan nama 'wazuh_alerts.csv' di folder ini.")
    exit()

print("Membaca data...")
df = pd.read_csv(file_csv)

# --- 2. PREPROCESSING & LABELING OTOMATIS ---
# Kita asumsikan peringatan dengan level >= 5 adalah "Serangan Nyata" (1), dan sisanya "Normal" (0)
# Catatan: Jika Anda membuat kolom 'is_attack' secara manual di Excel, Anda bisa menghapus baris ini.
if 'rule.level' in df.columns:
    df['is_attack'] = df['rule.level'].apply(lambda x: 1 if x >= 5 else 0)
else:
    print("⚠️ Kolom 'rule.level' tidak ditemukan! Pastikan Anda mengekspor kolom yang benar.")
    exit()

# Menghapus baris yang kosong (NaN) pada deskripsi peringatan
df = df.dropna(subset=['rule.description'])

X_text = df['rule.description']
y = df['is_attack']

print(f"Total Data: {len(df)} baris")
print(f"Total Serangan (1): {len(df[df['is_attack'] == 1])}")
print(f"Total Normal (0): {len(df[df['is_attack'] == 0])}")

# --- 3. EKSTRAKSI FITUR (Teks ke Angka) ---
print("\nMengubah teks log menjadi vektor...")
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

print("\n=== HASIL UJIAN MODEL AI ===")
print(f"Akurasi Model: {akurasi * 100:.2f}%")
print("\nDetail Laporan (Precision, Recall, F1-Score):")
print(classification_report(y_test, y_pred))

# --- 6. MENYIMPAN MODEL ---
# Menyimpan otak AI dan kamus kata (vectorizer) ke file agar bisa dipanggil oleh SOAR/Web API nanti
joblib.dump(model, 'ai_soc_model.pkl')
joblib.dump(vectorizer, 'vectorizer.pkl')

print("✅ Selesai! Model berhasil disimpan sebagai 'ai_soc_model.pkl' dan 'vectorizer.pkl'")
