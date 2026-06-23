import paramiko
import sys

# ============================================================
# KONFIGURASI - Ganti dengan kredensial server Anda
# ============================================================
host = 'YOUR_WAZUH_MANAGER_IP'
username = 'YOUR_SSH_USERNAME'
password = 'YOUR_SSH_PASSWORD'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=22, username=username, password=password)

def run_cmd(cmd, use_sudo=False):
    if use_sudo:
        cmd = f"echo '{password}' | sudo -S " + cmd
    print(f"Running: {cmd[:80]}...")
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    if exit_status != 0:
        print(f"Error: {err}")
    return out

print("--- 1. Training AI Model secara remote di Server ---")
train_script = """
import pandas as pd
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import joblib

logs = []
with open('/var/ossec/logs/alerts/2026/Jun/ossec-alerts-22.json', 'r') as f:
    for line in f:
        try:
            data = json.loads(line)
            desc = data.get('rule', {}).get('description', '')
            level = int(data.get('rule', {}).get('level', 1))
            is_attack = 1 if level >= 5 else 0
            logs.append({'desc': desc, 'is_attack': is_attack})
        except: pass

df = pd.DataFrame(logs)
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['desc'])
y = df['is_attack']

model = RandomForestClassifier()
model.fit(X, y)

joblib.dump(model, '/home/admin_soc/ai_soc_model.pkl')
joblib.dump(vectorizer, '/home/admin_soc/vectorizer.pkl')
"""
run_cmd(f"""cat << 'EOF' > /home/admin_soc/train_remote.py
{train_script}
EOF""")
run_cmd("/home/admin_soc/ai_env/bin/python /home/admin_soc/train_remote.py", use_sudo=True)

print("--- 2. Membuat Flask API ---")
api_script = """
from flask import Flask, request, jsonify
import joblib
import sys

app = Flask(__name__)
model = joblib.load('/home/admin_soc/ai_soc_model.pkl')
vectorizer = joblib.load('/home/admin_soc/vectorizer.pkl')

@app.route('/cek_log', methods=['POST'])
def cek_log():
    try:
        data = request.json
        desc = data.get('rule', {}).get('description', '')
        vektor = vectorizer.transform([desc])
        prediksi = model.predict(vektor)
        if prediksi[0] == 1:
            return jsonify({"status": "True Positive"})
        else:
            return jsonify({"status": "False Positive"})
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
"""
run_cmd(f"""cat << 'EOF' > /home/admin_soc/api_ai.py
{api_script}
EOF""")

print("--- 3. Mendaftarkan Flask API ke Systemd Service ---")
service_file = """[Unit]
Description=AI SOC Flask API
After=network.target

[Service]
User=root
WorkingDirectory=/home/admin_soc
ExecStart=/home/admin_soc/ai_env/bin/python /home/admin_soc/api_ai.py
Restart=always

[Install]
WantedBy=multi-user.target
"""
run_cmd(f"""cat << 'EOF' > /home/admin_soc/ai_api.service
{service_file}
EOF""")
run_cmd("mv /home/admin_soc/ai_api.service /etc/systemd/system/", use_sudo=True)
run_cmd("systemctl daemon-reload && systemctl enable ai_api && systemctl restart ai_api", use_sudo=True)

print("--- 4. Membuat Script Integrasi Wazuh ---")
integration_script = """#!/usr/bin/env python3
import sys, json, requests

def main():
    try:
        alert_file = sys.argv[1]
        with open(alert_file, 'r') as f:
            alert = json.load(f)
        
        resp = requests.post("http://127.0.0.1:5000/cek_log", json=alert, timeout=3)
        result = resp.json()
        
        if result.get("status") == "True Positive":
            srcip = alert.get("data", {}).get("srcip", "")
            if not srcip:
                srcip = "127.0.0.1"
                
            desc = alert.get("rule", {}).get("description", "")
            log_entry = f"WAZUH_AI_ALERT: True Positive. IP: {srcip} DESC: {desc}\\n"
            
            with open("/var/log/ai_alerts.log", "a") as f:
                f.write(log_entry)
    except Exception as e:
        pass

if __name__ == "__main__":
    main()
"""
run_cmd(f"""cat << 'EOF' > /home/admin_soc/custom-ai
{integration_script}
EOF""")
run_cmd("mv /home/admin_soc/custom-ai /var/ossec/integrations/", use_sudo=True)
run_cmd("chmod 750 /var/ossec/integrations/custom-ai", use_sudo=True)
run_cmd("chown root:wazuh /var/ossec/integrations/custom-ai", use_sudo=True)
run_cmd("touch /var/log/ai_alerts.log", use_sudo=True)
run_cmd("chown wazuh:wazuh /var/log/ai_alerts.log", use_sudo=True)

print("--- 5. Mengedit File Konfigurasi Wazuh ---")
xml_modifier = """
import re

# Modifikasi ossec.conf
conf_path = '/var/ossec/etc/ossec.conf'
with open(conf_path, 'r') as f:
    conf = f.read()

if '<name>custom-ai</name>' not in conf:
    integration_block = '''
  <!-- AI SOC Integration -->
  <integration>
    <name>custom-ai</name>
    <hook_url>http://127.0.0.1:5000/cek_log</hook_url>
    <alert_format>json</alert_format>
  </integration>

  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/ai_alerts.log</location>
  </localfile>

  <active-response>
    <command>firewall-drop</command>
    <location>local</location>
    <rules_id>100005</rules_id>
    <timeout>600</timeout>
  </active-response>
</ossec_config>'''
    conf = conf.replace('</ossec_config>', integration_block)
    with open(conf_path, 'w') as f:
        f.write(conf)

# Modifikasi local_rules.xml
rules_path = '/var/ossec/etc/rules/local_rules.xml'
with open(rules_path, 'r') as f:
    rules = f.read()

if 'id="100005"' not in rules:
    rule_block = '''
  <rule id="100005" level="12">
    <match>WAZUH_AI_ALERT: True Positive</match>
    <description>AI SOC DETECTED ATTACK: True Positive. Memblokir IP.</description>
  </rule>
</group>'''
    rules = rules.replace('</group>', rule_block)
    with open(rules_path, 'w') as f:
        f.write(rules)
"""
run_cmd(f"""cat << 'EOF' > /home/admin_soc/modify_xml.py
{xml_modifier}
EOF""")
run_cmd("python3 /home/admin_soc/modify_xml.py", use_sudo=True)

print("--- 6. Merestart Wazuh Manager ---")
run_cmd("systemctl restart wazuh-manager", use_sudo=True)
print("--- SEMUA PROSES SELESAI ---")
client.close()
