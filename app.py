import os
import sys
import tempfile
import streamlit as st

# .env yükle
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from analyzer import StaticAnalyzer
from llm_reviewer import LLMReviewer, AIReviewResult
from reporter import Reporter

# ---------------------------------------------------------------------------
# Streamlit Sayfa Yapılandırması
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Code Review Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# CSS Stilleri
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        color: #1E88E5;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .card-high {
        background-color: #FFEBEE;
        border-left: 5px solid #E53935;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 0.8rem;
    }
    .card-medium {
        background-color: #FFF8E1;
        border-left: 5px solid #FB8C00;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 0.8rem;
    }
    .card-low {
        background-color: #E8F5E9;
        border-left: 5px solid #43A047;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 0.8rem;
    }
    .badge-high { color: #E53935; font-weight: bold; }
    .badge-medium { color: #FB8C00; font-weight: bold; }
    .badge-low { color: #43A047; font-weight: bold; }
    .suggestion-text { color: #555; font-style: italic; font-size: 0.93rem; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Başlık
# ---------------------------------------------------------------------------
st.markdown('<div class="main-header">⚡ AI Code Review Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Yapay Zekâ ve Statik Analiz Destekli Kod İnceleme Sistemi</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Yan Menü (Sidebar)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Ayarlar & Girdi")

    source_type = st.radio("Kod Kaynağı Seçin:", ["Örnek Dosyalar", "Dosya Yükle", "Kod Yapıştır"])

    code_content = ""
    file_display_name = ""

    if source_type == "Örnek Dosyalar":
        examples_dir = "examples"
        available_files = []
        if os.path.exists(examples_dir):
            available_files = [f for f in os.listdir(examples_dir) if f.endswith(".py")]

        selected_example = st.selectbox("Örnek Dosya Seç:", available_files if available_files else ["hatali_kod.py"])
        if selected_example:
            example_path = os.path.join(examples_dir, selected_example)
            if os.path.exists(example_path):
                with open(example_path, "r", encoding="utf-8") as f:
                    code_content = f.read()
                file_display_name = selected_example

    elif source_type == "Dosya Yükle":
        uploaded_file = st.file_uploader("Python Dosyası Yükleyin (.py)", type=["py"])
        if uploaded_file is not None:
            code_content = uploaded_file.getvalue().decode("utf-8", errors="replace")
            file_display_name = uploaded_file.name

    elif source_type == "Kod Yapıştır":
        code_content = st.text_area("Python Kodunu Buraya Yapıştırın:", height=250, value="def hello():\n    eval('print(123)')\n")
        file_display_name = "snippet.py"

    st.markdown("---")
    enable_ai = st.checkbox("AI İncelemesi Aktif", value=True)

    selected_model = st.text_input("AI Model:", value=os.getenv("OPENAI_MODEL", "groq/compound-mini"))
    api_key = os.getenv("OPENAI_API_KEY", "")

    if enable_ai:
        if api_key:
            st.success("API Anahtarı Algılandı ✓")
        else:
            st.warning("API Anahtarı Bulunamadı! (.env veya ortam değişkeni)")

    analyze_button = st.button("🔍 Kodu Analiz Et", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Analiz Mantığı & Görüntüleme
# ---------------------------------------------------------------------------
if analyze_button or "last_result" in st.session_state:

    if analyze_button:
        if not code_content.strip():
            st.error("Lütfen analiz edilecek geçerli bir Python kodu girin.")
            st.stop()

        # Geçici dosyaya yazıp analiz et
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as tmp:
            tmp.write(code_content)
            tmp_path = tmp.name

        with st.spinner("🔍 Statik analiz çalışıyor..."):
            static_analyzer = StaticAnalyzer()
            static_result = static_analyzer.analyze(tmp_path)
            static_result.filepath = file_display_name

        ai_result = AIReviewResult(skipped=True, error="AI incelemesi kapalı")
        if enable_ai:
            with st.spinner("🤖 AI kod incelemesi yapılıyor..."):
                llm_reviewer = LLMReviewer()
                if selected_model:
                    llm_reviewer.model = selected_model
                ai_result = llm_reviewer.review(source_code=code_content, filepath=file_display_name)

        # Raporu da kaydet
        reporter = Reporter(static_result, ai_result)
        report_path = reporter.save_report()

        try:
            os.remove(tmp_path)
        except OSError:
            pass

        st.session_state["last_result"] = {
            "static": static_result,
            "ai": ai_result,
            "code": code_content,
            "filename": file_display_name,
            "report_path": report_path
        }

    res = st.session_state["last_result"]
    static_res = res["static"]
    ai_res = res["ai"]

    # --- ÖZET METRİKLERİ ---
    st.markdown("### 📊 Analiz Özeti")

    all_findings = list(static_res.findings)
    if not ai_res.skipped and not ai_res.error:
        all_findings += ai_res.findings

    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in all_findings:
        sev = getattr(f, "severity", "LOW").upper()
        counts[sev] = counts.get(sev, 0) + 1

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Toplam Satır", static_res.total_lines)
    col2.metric("Fonksiyon", static_res.function_count)
    col3.metric("Sınıf", static_res.class_count)
    col4.metric("🔴 High Risk", counts["HIGH"])
    col5.metric("🟡 Medium Risk", counts["MEDIUM"])
    col6.metric("🟢 Low Risk", counts["LOW"])

    st.markdown("---")

    # --- TABLAR ---
    tab_static, tab_ai, tab_code, tab_report = st.tabs([
        "🔍 Statik Analiz Bulguları",
        "🤖 AI Review Bulguları",
        "📄 Kaynak Kod",
        "📝 Rapor & Kayıtlar"
    ])

    # TAB 1: Statik Analiz
    with tab_static:
        st.markdown("#### 🔍 Python AST Statik Analiz Bulguları")
        if static_res.syntax_error:
            st.error(f"⚠️ Syntax Hatası: {static_res.syntax_error}")
        elif not static_res.findings:
            st.success("✅ Statik analiz herhangi bir kural ihlali tespit etmedi.")
        else:
            for f in static_res.findings:
                sev = f.severity.upper()
                card_class = "card-high" if sev == "HIGH" else ("card-medium" if sev == "MEDIUM" else "card-low")
                badge_class = "badge-high" if sev == "HIGH" else ("badge-medium" if sev == "MEDIUM" else "badge-low")
                badge_symbol = "[!]" if sev == "HIGH" else ("[" if sev == "MEDIUM" else "[-]")

                line_str = f"Line {f.line}" if f.line else "Genel"

                st.markdown(f"""
                <div class="{card_class}">
                    <span class="{badge_class}">{badge_symbol} [{sev}]</span> <b>{f.category}</b> &nbsp;|&nbsp; <code>{line_str}</code>
                    <br><span style="font-size:1rem; margin-top:4px; display:inline-block;">{f.message}</span>
                    {f'<br><span class="suggestion-text"><b>>> Öneri:</b> {f.suggestion}</span>' if f.suggestion else ''}
                </div>
                """, unsafe_allow_html=True)

    # TAB 2: AI Review
    with tab_ai:
        st.markdown("#### 🤖 Yapay Zekâ Kod İnceleme Bulguları")
        if ai_res.skipped:
            st.info(f"ℹ️ {ai_res.error}")
        elif ai_res.error:
            st.error(f"❌ {ai_res.error}")
        elif ai_res.parse_failed:
            st.warning("⚠️ Model cevap verdi ancak yanıt ayrıştırılamadı.")
            with st.expander("Ham Yanıt Önizleme"):
                st.text(ai_res.raw_response[:1000])
        elif not ai_res.findings:
            st.success("✅ AI herhangi bir potansiyel problem tespit etmedi.")
        else:
            for f in ai_res.findings:
                sev = f.severity.upper()
                card_class = "card-high" if sev == "HIGH" else ("card-medium" if sev == "MEDIUM" else "card-low")
                badge_class = "badge-high" if sev == "HIGH" else ("badge-medium" if sev == "MEDIUM" else "badge-low")
                badge_symbol = "[!]" if sev == "HIGH" else ("[" if sev == "MEDIUM" else "[-]")

                meta_parts = []
                if f.line_range:
                    meta_parts.append(f"Line: {f.line_range}")
                if f.function_name:
                    meta_parts.append(f"fn: {f.function_name}")
                meta_str = " | ".join(meta_parts) if meta_parts else ""

                st.markdown(f"""
                <div class="{card_class}">
                    <span class="{badge_class}">{badge_symbol} [{sev}]</span> <b>{f.category}</b> {f'&nbsp;|&nbsp; <code>{meta_str}</code>' if meta_str else ''}
                    <br><span style="font-size:1rem; margin-top:4px; display:inline-block;">{f.message}</span>
                    {f'<br><span class="suggestion-text"><b>>> Çözüm Önerisi:</b> {f.suggestion}</span>' if f.suggestion else ''}
                </div>
                """, unsafe_allow_html=True)

    # TAB 3: Kaynak Kod
    with tab_code:
        st.markdown(f"#### 📄 Incelenen Dosya: `{res['filename']}`")
        st.code(res["code"], language="python", line_numbers=True)

    # TAB 4: Raporlar
    with tab_report:
        st.markdown("#### 📝 Analiz Raporu")
        report_path = res.get("report_path")
        if report_path and os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                report_txt = f.read()

            st.download_button(
                label="📥 TXT Raporunu İndir",
                data=report_txt,
                file_name=os.path.basename(report_path),
                mime="text/plain",
                type="primary"
            )

            st.text_area("Rapor Önizleme:", value=report_txt, height=400)
else:
    st.info("👈 Analizi başlatmak için yan menüden bir dosya seçin/yükleyin ve **🔍 Kodu Analiz Et** butonuna tıklayın.")
