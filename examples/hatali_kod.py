import os
import subprocess
import json
import hashlib
import requests
import pickle


# --- HATA 1: Hard-coded credentials (HIGH x3) ---
API_KEY    = "sk-abc123XYZ789secretvalue"
db_password = "S3cr3tP@ssw0rd!"
auth_token  = "ghp_realTokenHere1234567890"


# --- HATA 2: eval() kullanımı (HIGH) ---
def hesapla(ifade):
    return eval(ifade)


# --- HATA 3: exec() kullanımı (HIGH) ---
def kod_calistir(kaynak):
    exec(kaynak)


# --- HATA 4: subprocess shell=True (HIGH) ---
def komutu_calistir(komut):
    sonuc = subprocess.run(komut, shell=True, capture_output=True, text=True)
    return sonuc.stdout


# --- HATA 5: os.system() (MEDIUM) ---
def temizle():
    os.system("rm -rf /tmp/uygulama_cache")


# --- HATA 6: os.popen() (MEDIUM) ---
def sistem_bilgisi():
    return os.popen("uname -a").read()


# --- HATA 7: Çok fazla parametre (LOW) ---
def kullanici_olustur(ad, soyad, email, telefon, adres, sehir, ulke, posta_kodu):
    return {
        "ad": ad, "soyad": soyad, "email": email,
        "telefon": telefon, "adres": adres, "sehir": sehir,
        "ulke": ulke, "posta_kodu": posta_kodu,
    }


# --- HATA 8: Çıplak except: (MEDIUM) ---
def dosya_oku(yol):
    try:
        with open(yol) as f:
            return json.load(f)
    except:
        return {}


# --- HATA 9: except Exception (LOW) ---
def veritabani_baglan(host):
    try:
        return requests.get(host)
    except Exception:
        return None


# --- HATA 10: Aşırı iç içe geçme derinliği > 4 (MEDIUM) ---
def ic_ice_mantik(veri):
    if veri:
        for kayit in veri:
            if isinstance(kayit, dict):
                for anahtar, deger in kayit.items():
                    if deger is not None:
                        if isinstance(deger, list):
                            for eleman in deger:
                                if eleman > 0:
                                    print(f"{anahtar}={eleman}")


# --- HATA 11: Çok uzun fonksiyon (MEDIUM) ---
def her_seyi_yap(girdi):
    temiz = girdi.strip()
    if not temiz:
        return None

    if len(temiz) < 3:
        print("Çok kısa")
        return None

    if len(temiz) > 1000:
        print("Çok uzun")
        return None

    parcalar = temiz.split(",")
    sonuc = []
    for parca in parcalar:
        parca = parca.strip()
        if parca:
            sonuc.append(parca)

    donusturulmus = []
    for ogre in sonuc:
        ogre = ogre.upper()
        ogre = ogre.replace(" ", "_")
        donusturulmus.append(ogre)

    filtrelenmis = []
    for ogre in donusturulmus:
        if not ogre.startswith("_"):
            filtrelenmis.append(ogre)

    filtrelenmis.sort()

    bicimlendirilmis = []
    for i, ogre in enumerate(filtrelenmis):
        bicimlendirilmis.append(f"{i+1}. {ogre}")

    cikti = "\n".join(bicimlendirilmis)

    print(f"İşlendi: {len(bicimlendirilmis)} öğe")

    with open("log.txt", "a") as f:
        f.write(f"her_seyi_yap çağrıldı, {len(bicimlendirilmis)} sonuç\n")

    return cikti


# --- HATA 12: Hard-coded secret sınıf içinde (HIGH) ---
class VeriIsleyici:
    def __init__(self):
        self.gizli_anahtar = "hardcoded-secret-key-12345"
        self.client_secret = "another-secret-value-9876"

    def veri_cek(self, url):
        response = requests.get(url)
        return response.json()

    def isle(self, ham_veri):
        kod = ham_veri.get("kod", "")
        exec(kod)

    def sifrele(self, veri):
        return hashlib.md5(veri.encode()).hexdigest()

    def serialize_et(self, nesne):
        return pickle.dumps(nesne)

    def deserialize_et(self, veri):
        return pickle.loads(veri)
