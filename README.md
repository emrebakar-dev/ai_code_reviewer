# ⚡ AI Code Review Assistant

Python dosyalarını **iki aşamalı (Statik Analiz + Yapay Zekâ)** olarak inceleyen, hem **Web Arayüzü (Streamlit UI)** hem de **Terminal (CLI)** destekli modüler kod inceleme aracı.

---

## 🎯 Projenin Amacı

Yalnızca LLM'e kod gönderip yorum almak yerine, iki aşamalı bir analiz mimarisi kullanır:
1. **Statik Kod Analizi:** Python `ast` modülü ile kod çalıştırılmadan deterministik ve kesin güvenlik/kalite bulgularının tespiti.
2. **AI Code Review:** OpenAI uyumlu LLM API (Groq, Ollama, Gemini vb.) ile potansiyel hatalar, okunabilirlik ve sürdürülebilirlik incelemesi.

Statik analiz sonuçları ile AI sonuçları raporda birbirinden açıkça ayrılır.

---

## ✨ Özellikler

### 🔍 Statik Analiz (LLM/İnternet Bağımsız)
- **Syntax Hataları:** Parse edilemeyen kodların tespiti.
- **Tehlikeli Fonksiyonlar:** `eval()`, `exec()` kullanımı.
- **Kabuk Enjeksiyon Riskleri:** `subprocess(..., shell=True)`, `os.system()`, `os.popen()` kullanımı.
- **Hard-coded Secrets:** API key, password, token, private key tespiti.
- **Exception Yönetimi:** Çıplak `except:` veya genel `except Exception:` kullanımı.
- **Kod Kokuları:** 50+ satır uzun fonksiyonlar, 6+ parametre alan imzalar, 4+ derinlikte iç içe geçmiş mantık blokları.

### 🤖 AI Code Review
- **Kategoriler:** Potential Bugs, Security, Performance, Code Quality, Readability, Maintainability.
- **Önem Seviyeleri:** `HIGH`, `MEDIUM`, `LOW`.
- **Otomatik Onarım (Auto-Repair):** Yanıt yarım kalsa bile kesintiye uğramış JSON'u otomatik onarır.
- **Hızlı Entegrasyon:** Groq, Ollama (Local), Gemini veya OpenAI ile tam uyumlu.

### 📊 Arayüz ve Raporlama
- **Web UI (Streamlit):** Görsel kartlar, dosya yükleme/kod yapıştırma, renkli risk sayaçları ve canlı rapor indirme.
- **Terminal (CLI):** ANSI renkli ve sembollü düzenli çıktı.
- **TXT Raporu:** Her analiz sonunda `reports/` klasörüne zaman damgalı `.txt` rapor kaydı.

---

## 🚀 Kurulum

### 1. Depoyu klonlayın

```bash
git clone https://github.com/KULLANICI_ADI/ai_code_reviewer.git
cd ai_code_reviewer
```

### 2. Virtual Environment Oluşturma

```bash
python3 -m venv venv
source venv/bin/activate       # macOS / Linux
# venv\Scripts\activate        # Windows
```

### 3. Bağımlılıkların Kurulumu

```bash
pip install -r requirements.txt
```

### 4. `.env` Yapılandırması

Ortam dosyasını kopyalayın:

```bash
cp .env.example .env
```

`.env` dosyasını açıp API key'inizi girin (Groq ücretsizdir):

```env
OPENAI_API_KEY=gsk_your_groq_api_key_here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=groq/compound-mini
```

> **Not:** API key girilmezse AI taraması otomatik atlanır; statik analiz kesintisiz çalışmaya devam eder.

---

## 📖 Kullanım

### 1. Web Arayüzü (Streamlit UI)

```bash
streamlit run app.py
```
> Otomatik olarak tarayıcınızda açılır (`http://localhost:8501`). Dosya yükleyebilir, kod yapıştırabilir veya örnek dosyaları görsel olarak inceleyebilirsiniz.

### 2. Terminal (CLI) Kullanımı

```bash
# Tam analiz (Statik + AI)
python main.py examples/hatali_kod.py

# Sadece statik analiz (AI olmadan)
python main.py examples/hatali_kod.py --no-ai
```

---

## 🏗️ Proje Mimarisi

```
ai_code_reviewer/
├── app.py           # Streamlit tabanlı Web Arayüzü
├── main.py          # Terminal (CLI) giriş noktası
├── analyzer.py      # Statik kod analizörü (AST tabanlı)
├── llm_reviewer.py  # LLM entegrasyonu (OpenAI / Groq / Ollama API)
├── reporter.py      # Terminal & TXT rapor üretici
├── requirements.txt # Python bağımlılıkları
├── .env.example     # Örnek ortam değişkenleri şablonu
├── .gitignore       # Git yoksayma kuralları (API key gizleme dahil)
├── README.md        # Proje dokümantasyonu
├── examples/        # Test için örnek hatalı Python dosyaları
└── reports/         # Otomatik oluşturulan zaman damgalı analiz raporları
```

---

## 📝 Lisans

MIT
