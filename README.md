# AI Code Review Assistant

Python, C/C++ ve Java kaynak kodlarını **iki aşamalı (Statik Analiz + Yapay Zekâ)** olarak inceleyen, hem **Web Arayüzü (Streamlit UI)** hem de **Terminal (CLI)** destekli çok dilli ve modüler kod inceleme aracı.

---

## Projenin Amacı

Yalnızca LLM'e kod gönderip yorum almak yerine, iki aşamalı bir analiz mimarisi kullanır:
1. **Statik Kod Analizi:** Python için `ast` modülü, C/C++ ve Java için özel regex kural motorları ile kod çalıştırılmadan deterministik ve kesin güvenlik/kalite bulgularının tespiti.
2. **AI Code Review:** OpenAI uyumlu LLM API (Groq, Qwen, Ollama vb.) ile dilden bağımsız potansiyel hatalar, okunabilirlik ve sürdürülebilirlik incelemesi.

Statik analiz sonuçları ile AI sonuçları raporda birbirinden açıkça ayrılır.

---

## Özellikler

### Desteklenen Diller
- **Python:** `.py`
- **C / C++:** `.c`, `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`
- **Java:** `.java`

### Statik Analiz (LLM/İnternet Bağımsız)
- **Python:** Syntax hataları, `eval()`, `exec()`, `subprocess(..., shell=True)`, `os.system()`, `os.popen()`, çıplak `except:`, hard-coded secrets, uzun fonksiyonlar, fazla parametreler, derin iç içe geçmiş kodlar.
- **C / C++:** Buffer Overflow riskleri (`strcpy`, `strcat`, `gets`, `sprintf`), Kabuk Enjeksiyonu (`system()`), Format String Açıkları (`printf(var)`), Bellek Güvenliği (`malloc`/`realloc` NULL kontrolü ve free uyarısı, raw `new` kullanımı), Hard-coded C/C++ secrets.
- **Java:** SQL Injection tespiti, `Runtime.exec()` ve `ProcessBuilder` güvenliği, `ObjectInputStream` güvensiz deserialization, `printStackTrace()` ile sızıntı tespiti, boş `catch` blokları, `String ==` referans karşılaştırma uyarısı, hassas log yazımı.

### False-Positive (Hatalı Bulgu) Filtreleme
- **Inline Suppression:** `# noreview` (Python) veya `// noreview` (C/C++/Java) etiketi içeren satırlar statik analizden tamamen muaf tutulur.
- **Deduplication:** Aynı satır ve kategorideki tekrarlayan bulgular otomatik tekilleştirilir.
- **Placeholder & Kısa Değer Filtresi:** `"changeme"`, `"your_key_here"`, `"example"`, `"password"` gibi test/placeholder değerler gerçek secret olarak işaretlenmez.
- **Confidence Score & UI Slider:** Her bulguya güven skoru atanır (0.0 - 1.0); arayüzdeki slider ile düşük güvenli bulgular gizlenebilir.

### Tüm Klasör / Proje Taraması
- **CLI:** `python main.py --dir /proje_klasoru/` komutu ile tüm proje özyinelemeli (recursive) taranır.
- **Web UI:** İster bilgisayarınızdaki yerel klasör yolunu yapıştırın, ister projenizi `.zip` olarak yükleyin.
- Toplu proje bulgu özeti, en riskli dosyalar sıralaması ve tek tıkla indirilebilir birleşik proje raporu.

### AI Code Review
- **Model:** `qwen/qwen3.6-27b` veya Groq üzerindeki diğer OpenAI-uyumlu LLM modelleri.
- **Kategoriler:** Potential Bugs, Security, Performance, Code Quality, Readability, Maintainability.
- **Auto-Repair:** Kesintiye uğramış JSON yanıtlarını otomatik onarır.
- **Rate-Limit Koruması:** Dosyalar arası otomatik bekleme ve üstel geri çekilme (exponential backoff) ile API kotası korunur.

---

## Kurulum

### 1. Depoyu klonlayın

```bash
git clone https://github.com/emrebakar-dev/ai_code_reviewer.git
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
OPENAI_MODEL=qwen/qwen3.6-27b
```

> **Not:** API key girilmezse AI taraması otomatik atlanır; statik analiz kesintisiz çalışmaya devam eder.

---

## Kullanım

### 1. Web Arayüzü (Streamlit UI)

```bash
streamlit run app.py
```
> Otomatik olarak tarayıcınızda açılır (`http://localhost:8501`). Tek dosya yükleyebilir, kod yapıştırabilir veya bir projenin klasör yolunu girerek tüm projeyi taratabilirsiniz.

### 2. Terminal (CLI) Kullanımı

```bash
# Tek dosya analizi (Python, C/C++, Java)
python main.py examples/hatali_kod.py
python main.py examples/hatali_kod.cpp
python main.py examples/hatali_kod.java

# Yalnızca statik analiz (AI olmadan)
python main.py examples/hatali_kod.py --no-ai

# Tüm proje / klasör taraması
python main.py --dir /path/to/project

# Klasör taraması (AI olmadan)
python main.py --dir /path/to/project --no-ai
```

---

## Raporlama

Yapılan her analiz sonunda `reports/` klasörüne zaman damgalı `.txt` rapor kaydedilir:
- `reports/code_review_YYYY_MM_DD_HHMM.txt` (Tek dosya raporu)
- `reports/project_review_YYYY_MM_DD_HHMM.txt` (Toplu proje raporu)
