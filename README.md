# AI Code Reviewer

AI Code Reviewer, yazılımlarınızdaki güvenlik zafiyetlerini, kod kalitesi ihlallerini, performans ve karmaşıklık problemlerini hem statik analiz kuralları hem de yapay zekâ (Groq / Qwen LLM) desteğiyle otomatik olarak tespit eden çok dilli bir kod inceleme platformudur.

---

## Öne Çıkan Özellikler

- **Çok Dilli Statik Analiz**:
  - **Python**: AST tabanlı analiz (eval/exec, subprocess shell=True, hardcoded secrets, bare except, cyclomatic complexity, uzun fonksiyonlar).
  - **C / C++**: Buffer overflow (strcpy/sprintf), format string açıkları, kabuk enjeksiyonu (system()), bellek yönetimi (RAII/unique_ptr önerisi).
  - **Java**: SQL Injection, güvensiz deserialization (readObject), printStackTrace sızıntıları, boş catch blokları, String == hataları.
  - **Web & Frontend (CSS / HTML / JS / TS)**:
    - **CSS**: !important aşırı kullanımı, güvensiz HTTP asset yüklemeleri, @import performans riski, aşırı yüksek z-index.
    - **JavaScript / TypeScript**: innerHTML XSS zafiyetleri, document.write, localStorage üzerinde token saklama, eval(), console.log sızıntıları.
    - **HTML**: Inline event handler'lar, target="_blank" rel="noopener" eksikliği, güvensiz HTTP script çağrıları, alt etiketi eksik resimler.
- **Yapay Zekâ (AI) İncelemesi**:
  - Groq API üzerinden çalışan Qwen 2.7B LLM entegrasyonu.
  - Yanlış pozitif (False-Positive) filtreleme, satır bazlı deduping ve noreview bastırma desteği.
- **Next.js 14 + FastAPI Modern Web Arayüzü**:
  - Vercel / Linear tasarım anlayışıyla hazırlanmış, ferah ve canlı dark studio teması.
  - Tek dosya yükleme, kod yapıştırma, yerel klasör yolu taraması ve ZIP arşivi yükleme modları.
  - Canlı % ilerleme çubuğu, HIGH / MEDIUM / LOW renk kodlu bulgu kartları ve tek tıkla TXT raporu indirme.
- **CLI (Komut Satırı) Desteği**:
  - Otomatik CI/CD veya lokal terminal taramaları için `--dir` ve `--no-ai` bayrakları.

---

## Proje Yapısı

```
ai_code_reviewer/
├── api.py               # FastAPI REST backend servisi
├── analyzer.py          # Python, C/C++, Java, CSS, HTML, JS/TS statik analiz motoru
├── scanner.py           # Çoklu dosya ve klasör tarama motoru
├── llm_reviewer.py      # Groq / Qwen AI inceleme modülü
├── reporter.py          # Konsol ve TXT rapor üretici
├── main.py              # CLI (Komut satırı) arayüzü
├── app.py               # Streamlit web arayüzü (yedek)
├── requirements.txt     # Python bağımlılıkları
├── examples/            # Örnek test dosyaları (.py, .cpp, .java, .css, .js)
└── frontend/            # Next.js 14 + Tailwind CSS web uygulaması
```

---

## Tek Tıkla Başlatma (En Kolay Yol)

**Masaüstünden Tek Tıkla Başlatma:**
Masaüstünüzde otomatik oluşan **`AI Code Reviewer.command`** kısayoluna çift tıklayın. 
Sistem hem FastAPI backend'ini hem de Next.js frontend'ini otomatik başlatacak ve tarayıcınızda `http://localhost:3000` adresini açacaktır.

**VS Code İçinden Başlatma:**
VS Code içinde `Cmd + Shift + B` tuşlarına basarak **🚀 AI Code Reviewer Başlat** görevini seçebilirsiniz.

---

## Kurulum


### 1. Depoyu Klonlayın
```bash
git clone https://github.com/emrebakar-dev/ai_code_reviewer.git
cd ai_code_reviewer
```

### 2. Python Sanal Ortamını Oluşturun ve Bağımlılıkları Yükleyin
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Çevre Değişkenlerini Ayarlayın
Kök dizinde `.env` dosyası oluşturun ve Groq API anahtarınızı ekleyin:
```env
OPENAI_API_KEY=your_groq_api_key_here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=qwen/qwen3.6-27b
```

---

## Çalıştırma Modları

### Mod 1: Next.js + FastAPI Web Arayüzü (Tavsiye Edilen)

**1. Terminal — FastAPI Backend Servisini Başlatın (Port 8000):**
```bash
source venv/bin/activate
uvicorn api:app --reload --port 8000
```

**2. Terminal — Next.js Frontend Uygulamasını Başlatın (Port 3000):**
```bash
cd frontend
npm install
npm run dev
```

Tarayıcınızda `http://localhost:3000` adresini açarak kullanabilirsiniz.

---

### Mod 2: CLI (Komut Satırı) Kullanımı

**Tek Dosya Analizi:**
```bash
python3 main.py --file examples/hatali_kod.py
```

**Tüm Proje / Klasör Taraması:**
```bash
python3 main.py --dir examples
```

**Yalnızca Statik Analiz (AI İncelemesini Kapatma):**
```bash
python3 main.py --dir examples --no-ai
```

---

### Mod 3: Streamlit Arayüzü (Yedek)
```bash
streamlit run app.py
```

---

## Yanlış Pozitifları Bastırma (Suppression)

Kodunuzda uyarı almak istemediğiniz satırların sonuna `# noreview` veya `// noreview` ekleyebilirsiniz:

```python
API_KEY = "dummy_test_key"  # noreview
```

```javascript
element.innerHTML = userInput; // noreview
```
