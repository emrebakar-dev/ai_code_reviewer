"""
bad_code.py
-----------
Statik analizör ve AI incelemesini test etmek için kasıtlı olarak
hatalı/kötü yazılmış örnek Python dosyası.

İçerdiği sorunlar:
  - Hard-coded API key ve password
  - eval() kullanımı
  - subprocess shell=True
  - Çıplak except: 
  - Çok uzun fonksiyon
  - Çok fazla parametre
  - Aşırı iç içe geçme
  - os.system() kullanımı
  - Genel Exception yakalama
  - Kod tekrarı ve kötü isimlendirme
"""

import os
import subprocess
import json
import requests


# ----------------------------------------------------------------
# Sorun 1: Hard-coded credentials
# ----------------------------------------------------------------
API_KEY  = "sk-abc123XYZ789secretvalue"
password = "SuperSecret123!"
db_token = "ghp_realTokenHere1234567890"


# ----------------------------------------------------------------
# Sorun 2: Çok fazla parametre + genel exception
# ----------------------------------------------------------------
def process_user_data(name, age, email, address, phone, country, zip_code, notes):
    """Kullanıcı verisini işler — çok fazla parametre."""
    try:
        result = {}
        result["name"] = name
        result["age"] = age
        result["email"] = email
        result["address"] = address
        result["phone"] = phone
        result["country"] = country
        result["zip_code"] = zip_code
        result["notes"] = notes
        return result
    except Exception:
        print("bir hata olustu")
        return None


# ----------------------------------------------------------------
# Sorun 3: eval() kullanımı
# ----------------------------------------------------------------
def calculate(expression):
    """Kullanıcıdan gelen ifadeyi eval ile hesaplar."""
    return eval(expression)


# ----------------------------------------------------------------
# Sorun 4: subprocess shell=True
# ----------------------------------------------------------------
def run_command(cmd):
    """Komutu shell=True ile çalıştırır."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout


# ----------------------------------------------------------------
# Sorun 5: os.system() kullanımı
# ----------------------------------------------------------------
def clean_temp():
    os.system("rm -rf /tmp/myapp_cache")


# ----------------------------------------------------------------
# Sorun 6: Aşırı iç içe geçme (derinlik > 4)
# ----------------------------------------------------------------
def deeply_nested_logic(data):
    """Aşırı iç içe geçmiş mantık."""
    if data:
        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    if value is not None:
                        if isinstance(value, list):
                            for element in value:
                                if element > 0:
                                    print(f"Found: {key}={element}")


# ----------------------------------------------------------------
# Sorun 7: Çıplak except:
# ----------------------------------------------------------------
def read_config(filepath):
    """Config dosyasını okur — çıplak except kullanıyor."""
    try:
        with open(filepath) as f:
            return json.load(f)
    except:
        return {}


# ----------------------------------------------------------------
# Sorun 8: Çok uzun fonksiyon (50+ satır)
# ----------------------------------------------------------------
def mega_function(input_data):
    """
    Her şeyi tek başına yapan, çok uzun fonksiyon.
    Tek sorumluluk ilkesini ihlal ediyor.
    """
    # Adım 1: Veriyi temizle
    cleaned = input_data.strip()
    if not cleaned:
        return None

    # Adım 2: Validate
    if len(cleaned) < 3:
        print("Çok kısa")
        return None
    if len(cleaned) > 1000:
        print("Çok uzun")
        return None

    # Adım 3: Parse
    parts = cleaned.split(",")
    result = []
    for part in parts:
        part = part.strip()
        if part:
            result.append(part)

    # Adım 4: Transform
    transformed = []
    for item in result:
        item = item.upper()
        item = item.replace(" ", "_")
        transformed.append(item)

    # Adım 5: Filter
    filtered = []
    for item in transformed:
        if not item.startswith("_"):
            filtered.append(item)

    # Adım 6: Sort
    filtered.sort()

    # Adım 7: Format
    formatted = []
    for i, item in enumerate(filtered):
        formatted.append(f"{i+1}. {item}")

    # Adım 8: Build output
    output = "\n".join(formatted)

    # Adım 9: Log
    print(f"Processed {len(formatted)} items")
    with open("log.txt", "a") as f:
        f.write(f"mega_function called, {len(formatted)} results\n")

    # Adım 10: Return
    return output


# ----------------------------------------------------------------
# Sorun 9: Tanımsız değişken kullanımı (runtime hatası)
# ----------------------------------------------------------------
def broken_function():
    x = undefined_variable + 1   # noqa — intentional for demo
    return x


# ----------------------------------------------------------------
# Sınıf örneği
# ----------------------------------------------------------------
class DataProcessor:
    """Veri işleme sınıfı — bazı sorunlar içeriyor."""

    def __init__(self):
        self.secret_key = "hardcoded-secret-key-12345"

    def fetch_data(self, url):
        """Veri çeker — hata yönetimi eksik."""
        response = requests.get(url)  # timeout yok
        return response.json()

    def process(self, raw):
        code = raw.get("code", "")
        # Sorun: exec ile dinamik kod çalıştırma
        exec(code)
