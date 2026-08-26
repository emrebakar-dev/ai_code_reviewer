import os
import sys
import tempfile
import zipfile
import shutil
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from analyzer import StaticAnalyzer
from llm_reviewer import LLMReviewer, AIReviewResult
from reporter import Reporter, ProjectReporter

st.set_page_config(
    page_title="AI Code Review Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Overall Layout & Background */
    .stApp {
        background-color: #0B0F17 !important;
        color: #E2E8F0;
    }

    /* Custom Top Navigation / Branding Header */
    .brand-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .brand-icon {
        background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        box-shadow: 0 4px 20px rgba(139, 92, 246, 0.3);
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #F8FAFC;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #94A3B8;
        margin: 0;
        font-weight: 400;
    }

    /* Override Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.07) !important;
    }

    /* Minimal Linear-style Findings Cards */
    .card-high {
        background: rgba(239, 68, 68, 0.06);
        border: 1px solid rgba(239, 68, 68, 0.25);
        border-left: 4px solid #EF4444;
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
        transition: all 0.2s ease-in-out;
    }
    .card-high:hover {
        border-color: rgba(239, 68, 68, 0.5);
        background: rgba(239, 68, 68, 0.1);
    }

    .card-medium {
        background: rgba(245, 158, 11, 0.06);
        border: 1px solid rgba(245, 158, 11, 0.25);
        border-left: 4px solid #F59E0B;
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
        transition: all 0.2s ease-in-out;
    }
    .card-medium:hover {
        border-color: rgba(245, 158, 11, 0.5);
        background: rgba(245, 158, 11, 0.1);
    }

    .card-low {
        background: rgba(16, 185, 129, 0.06);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-left: 4px solid #10B981;
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
        transition: all 0.2s ease-in-out;
    }
    .card-low:hover {
        border-color: rgba(16, 185, 129, 0.5);
        background: rgba(16, 185, 129, 0.1);
    }

    .badge-high {
        background: rgba(239, 68, 68, 0.2);
        color: #FCA5A5;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-medium {
        background: rgba(245, 158, 11, 0.2);
        color: #FDE68A;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-low {
        background: rgba(16, 185, 129, 0.2);
        color: #A7F3D0;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
    }

    .card-title {
        color: #F8FAFC;
        font-size: 1.05rem;
        font-weight: 600;
        margin-left: 8px;
    }
    .card-body-text {
        color: #CBD5E1;
        font-size: 0.98rem;
        margin-top: 8px;
        line-height: 1.5;
        display: block;
    }
    .suggestion-text {
        background: #0F172A;
        border: 1px solid #1E293B;
        padding: 8px 12px;
        border-radius: 6px;
        color: #38BDF8;
        font-size: 0.9rem;
        margin-top: 10px;
        display: block;
        font-family: 'Fira Code', monospace;
    }

    /* Custom Dashboard Metrics Boxes */
    div[data-testid="stMetric"] {
        background-color: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-weight: 700 !important;
    }

    /* Streamlit Tabs Customization */
    button[data-baseweb="tab"] {
        background: transparent !important;
        color: #94A3B8 !important;
        font-weight: 600 !important;
        border-bottom: 2px solid transparent !important;
    }
    button[aria-selected="true"] {
        color: #38BDF8 !important;
        border-bottom-color: #38BDF8 !important;
    }
</style>
""", unsafe_allow_html=True)



st.markdown("""
<div class="brand-container">
    <div class="brand-icon">⚡</div>
    <div>
        <div class="main-header">AI Code Review Assistant</div>
        <div class="sub-header">Statik Analiz + Yapay Zekâ Destekli Kod Güvenliği ve İnceleme Platformu</div>
    </div>
</div>
""", unsafe_allow_html=True)




def render_finding_card(f, confidence_threshold):
    conf = getattr(f, "confidence", 1.0)
    if conf < confidence_threshold:
        return
    sev = f.severity.upper()
    card_class = "card-high" if sev == "HIGH" else ("card-medium" if sev == "MEDIUM" else "card-low")
    badge_class = "badge-high" if sev == "HIGH" else ("badge-medium" if sev == "MEDIUM" else "badge-low")
    badge_symbol = "[!]" if sev == "HIGH" else ("[~]" if sev == "MEDIUM" else "[-]")
    conf_label = f"| güven: {conf:.0%}"
    line_str = f"Line {f.line}" if getattr(f, "line", None) else (f"Line {f.line_range}" if getattr(f, "line_range", None) else "Genel")
    suggestion = getattr(f, "suggestion", None)
    message = getattr(f, "message", "")

    # HTML injection / XSS önlemi: içerik doğrudan HTML'e gömülmeden escape edilmeli
    import html as _html
    safe_message    = _html.escape(str(message))
    safe_suggestion = _html.escape(str(suggestion)) if suggestion else None
    safe_category   = _html.escape(str(f.category))
    safe_line_str   = _html.escape(str(line_str))

    st.markdown(f"""
    <div class="{card_class}">
        <span class="{badge_class}">{badge_symbol} [{sev}]</span> <span class="card-title">{safe_category}</span> &nbsp;|&nbsp; <code>{safe_line_str}</code> <span style="color:#888;font-size:0.85rem">{conf_label}</span>
        <span class="card-body-text">{safe_message}</span>
        {f'<span class="suggestion-text"><b>>> Öneri:</b> {safe_suggestion}</span>' if safe_suggestion else ''}
    </div>
    """, unsafe_allow_html=True)



with st.sidebar:
    st.header("⚙️ Ayarlar & Girdi")

    source_type = st.radio(
        "Kaynak Türü:",
        ["Tek Dosya", "Proje / Klasör (ZIP)"],
        help="Tek dosya analizi veya tüm projeyi ZIP olarak yükleyin"
    )

    code_content = ""
    file_display_name = ""

    if source_type == "Tek Dosya":
        file_source = st.radio("Dosya Kaynağı:", ["Örnek Dosyalar", "Dosya Yükle", "Kod Yapıştır"])

        if file_source == "Örnek Dosyalar":
            examples_dir = "examples"
            valid_exts = (".py", ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".java")
            available_files = []
            if os.path.exists(examples_dir):
                available_files = [f for f in os.listdir(examples_dir) if f.endswith(valid_exts)]
            selected_example = st.selectbox("Örnek Dosya Seç:", available_files if available_files else ["hatali_kod.py"])
            if selected_example:
                example_path = os.path.join(examples_dir, selected_example)
                if os.path.exists(example_path):
                    with open(example_path, "r", encoding="utf-8") as f:
                        code_content = f.read()
                    file_display_name = selected_example

        elif file_source == "Dosya Yükle":
            uploaded_file = st.file_uploader(
                "Kaynak Dosya Yükle (.py, .c, .cpp, .java ...)",
                type=["py", "c", "cpp", "cc", "h", "hpp", "java"]
            )
            if uploaded_file is not None:
                code_content = uploaded_file.getvalue().decode("utf-8", errors="replace")
                file_display_name = uploaded_file.name

        elif file_source == "Kod Yapıştır":
            code_content = st.text_area("Kodu Buraya Yapıştırın:", height=250, value="def hello():\n    eval('print(123)')\n")
            file_display_name = "snippet.py"

    st.markdown("---")
    enable_ai = st.checkbox("AI İncelemesi Aktif", value=True)
    confidence_threshold = st.slider(
        "Minimum Güven Eşiği",
        min_value=0.0, max_value=1.0, value=0.0, step=0.05,
        help="Bu eşiğin altındaki bulgular gizlenir (0 = hepsi göster)"
    )
    selected_model = st.text_input("AI Model:", value=os.getenv("OPENAI_MODEL", "qwen/qwen3.6-27b"))
    api_key = os.getenv("OPENAI_API_KEY", "")

    if enable_ai:
        if api_key:
            st.success("API Anahtarı Algılandı ✓")
        else:
            st.warning("API Anahtarı Bulunamadı! (.env veya ortam değişkeni)")

    analyze_button = st.button("🔍 Analiz Et", type="primary", use_container_width=True)


# ─── PROJECT / ZIP MODE ───────────────────────────────────────────────────────
if source_type == "Proje / Klasör (ZIP)":
    st.markdown("### 📦 Proje / Klasör Taraması")

    proj_input_type = st.radio(
        "Klasör Girdi Yöntemi:",
        ["Yerel Klasör Yolu Gir", "ZIP Dosyası Yükle"],
        horizontal=True
    )

    zip_file = None
    dir_path_input = ""

    if proj_input_type == "ZIP Dosyası Yükle":
        st.info("Projenizi bir `.zip` dosyası olarak yükleyin. Desteklenen tüm dosyalar otomatik taranır.")
        zip_file = st.file_uploader("Proje ZIP Dosyası Yükle", type=["zip"])
    else:
        st.info("Bilgisayarınızdaki klasör yolunu girin. Arka planda tüm proje otomatik taranır.")
        dir_path_input = st.text_input(
            "Yerel Klasör Yolu:",
            value="",
            placeholder="./examples veya /Users/kullanici/Desktop/proje"
        )


    if analyze_button:
        target_dir = None
        tmp_dir = None

        if proj_input_type == "ZIP Dosyası Yükle" and zip_file:
            tmp_dir = tempfile.mkdtemp(prefix="aicr_project_")
            with zipfile.ZipFile(zip_file, "r") as zf:
                zf.extractall(tmp_dir)
            target_dir = tmp_dir
            proj_name = zip_file.name
        elif proj_input_type == "Yerel Klasör Yolu Gir" and dir_path_input.strip():
            if os.path.isdir(dir_path_input.strip()):
                target_dir = dir_path_input.strip()
                proj_name = os.path.basename(target_dir) or target_dir
            else:
                st.error(f"❌ Klasör bulunamadı: '{dir_path_input}'")

        if target_dir:
            try:
                from scanner import ProjectScanner

                progress_bar = st.progress(0, text="Dosyalar taranıyor...")
                status_text = st.empty()

                def ui_progress(i, total, filepath):
                    pct = int((i + 1) / total * 100)
                    rel = os.path.relpath(filepath, target_dir)
                    progress_bar.progress(pct, text=f"[{i+1}/{total}] {rel}")
                    status_text.caption(f"Taranan: {rel}")

                scanner = ProjectScanner(no_ai=not enable_ai, model=selected_model if selected_model else None)
                project_result = scanner.scan(target_dir, progress_callback=ui_progress)
                project_result.directory = proj_name

                progress_bar.progress(100, text="Tarama tamamlandı!")
                status_text.empty()

                report_path = ProjectReporter(project_result).save_report()
                st.session_state["project_result"] = project_result
                st.session_state["project_report_path"] = report_path
            finally:
                if tmp_dir:
                    shutil.rmtree(tmp_dir, ignore_errors=True)


    if "project_result" in st.session_state:
        pr = st.session_state["project_result"]

        st.markdown("### 📊 Proje Özeti")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Dosya Sayısı", pr.total_files)
        c2.metric("Toplam Satır", pr.total_lines)
        c3.metric("🔴 HIGH", pr.total_high)
        c4.metric("🟡 MEDIUM", pr.total_medium)
        c5.metric("🟢 LOW", pr.total_low)

        st.markdown("---")
        st.markdown("### 📋 Dosya Listesi (Risk Sırası)")

        for fr in pr.sorted_by_risk():
            rel = os.path.relpath(fr.filepath, ".") if os.path.exists(fr.filepath) else fr.filepath
            try:
                rel = fr.filepath.split(os.sep)[-1]
            except Exception:
                rel = fr.filepath

            lang = fr.static.language.upper()
            h, m, l = fr.high_count, fr.medium_count, fr.low_count
            total_f = fr.total_findings
            label = f"[{lang}] {rel}  —  🔴 H:{h}  🟡 M:{m}  🟢 L:{l}  (toplam: {total_f})"

            with st.expander(label, expanded=(h > 0)):
                if fr.static.syntax_error:
                    st.error(f"⚠️ Syntax Hatası: {fr.static.syntax_error}")

                if fr.static.findings:
                    st.markdown("**Statik Analiz Bulguları:**")
                    for f in fr.static.findings:
                        render_finding_card(f, confidence_threshold)
                else:
                    st.success("Statik analiz bulgusu yok.")

                if not fr.ai.skipped and not fr.ai.error and fr.ai.findings:
                    st.markdown("**AI Review Bulguları:**")
                    for f in fr.ai.findings:
                        render_finding_card(f, confidence_threshold)
                elif not fr.ai.skipped and not fr.ai.error and not fr.ai.findings:
                    if not getattr(fr.ai, "parse_failed", False):
                        st.success("AI inceleme bulgusu yok.")
                    else:
                        st.warning("⚠️ AI yanıt verdi ama ayrıştırılamadı.")
                elif fr.ai.error and not fr.ai.skipped:
                    st.error(f"❌ AI hatası: {fr.ai.error}")
                elif fr.ai.skipped:
                    st.caption(f"ℹ️ {fr.ai.error}")


        st.markdown("---")
        report_path = st.session_state.get("project_report_path")
        if report_path and os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                report_txt = f.read()
            st.download_button(
                label="📥 Proje Raporunu İndir (TXT)",
                data=report_txt,
                file_name=os.path.basename(report_path),
                mime="text/plain",
                type="primary"
            )
    elif not zip_file and not dir_path_input:
        st.caption("👆 Başlamak için yukarıdaki kutuya bir klasör yolu girin veya ZIP dosyası yükleyin.")


# ─── SINGLE FILE MODE ─────────────────────────────────────────────────────────
else:
    if analyze_button or "last_result" in st.session_state:

        if analyze_button:
            if not code_content.strip():
                st.error("Lütfen analiz edilecek geçerli bir kaynak kod girin.")
                st.stop()

            file_ext = os.path.splitext(file_display_name)[1] if file_display_name else ".py"
            if not file_ext:
                file_ext = ".py"

            with tempfile.NamedTemporaryFile(suffix=file_ext, mode="w", encoding="utf-8", delete=False) as tmp:
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
        col3.metric("Sınıf/Struct", static_res.class_count)
        col4.metric("🔴 High Risk", counts["HIGH"])
        col5.metric("🟡 Medium Risk", counts["MEDIUM"])
        col6.metric("🟢 Low Risk", counts["LOW"])

        st.markdown("---")

        tab_static, tab_ai, tab_code, tab_report = st.tabs([
            "🔍 Statik Analiz Bulguları",
            "🤖 AI Review Bulguları",
            "📄 Kaynak Kod",
            "📝 Rapor & Kayıtlar"
        ])

        with tab_static:
            if static_res.language == "java":
                lang_title = "Java Statik Analiz"
            elif static_res.language == "cpp":
                lang_title = "C/C++ Statik Analiz"
            else:
                lang_title = "Python AST Statik Analiz"
            st.markdown(f"#### 🔍 {lang_title} Bulguları")
            if static_res.syntax_error:
                st.error(f"⚠️ Syntax Hatası: {static_res.syntax_error}")
            elif not static_res.findings:
                st.success("✅ Statik analiz herhangi bir kural ihlali tespit etmedi.")
            else:
                visible = [f for f in static_res.findings if getattr(f, "confidence", 1.0) >= confidence_threshold]
                hidden_count = len(static_res.findings) - len(visible)
                if hidden_count > 0:
                    st.caption(f"ℹ️ {hidden_count} bulgu güven eşiği ({confidence_threshold:.2f}) altında gizlendi.")
                if not visible:
                    st.success("✅ Seçilen güven eşiğinde görüntülenecek bulgu yok.")
                for f in visible:
                    render_finding_card(f, 0.0)

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
                    render_finding_card(f, confidence_threshold)

        with tab_code:
            st.markdown(f"#### 📄 Incelenen Dosya: `{res['filename']}`")
            ext = os.path.splitext(res["filename"])[1].lstrip(".") or "python"
            st.code(res["code"], language=ext, line_numbers=True)

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
        st.markdown("""
        <div style="background: #111827; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 3rem 2rem; text-align: center; margin-top: 1rem;">
            <div style="display: inline-flex; align-items: center; justify-content: center; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.2); width: 60px; height: 60px; border-radius: 16px; margin-bottom: 1.2rem; font-size: 1.8rem;">
                ⚡
            </div>
            <h2 style="color: #F8FAFC; font-weight: 700; margin-bottom: 0.6rem; font-size: 1.6rem;">Analize Başlamaya Hazır Mısınız?</h2>
            <p style="color: #94A3B8; font-size: 1rem; max-width: 550px; margin: 0 auto 2rem auto; line-height: 1.6;">
                Sol menüden tek bir dosya yükleyin, projenizin yerel klasör yolunu yapıştırın veya ZIP olarak yükleyip <b>🔍 Analiz Et</b> butonuna tıklayın.
            </p>
            <div style="display: flex; justify-content: center; gap: 1.2rem; flex-wrap: wrap;">
                <div style="background: #1F2937; border: 1px solid rgba(255, 255, 255, 0.06); padding: 1.2rem 1rem; border-radius: 12px; width: 160px; text-align: center;">
                    <div style="font-size: 1.6rem;">🐍</div>
                    <div style="font-weight: 600; color: #F1F5F9; margin-top: 6px; font-size: 0.95rem;">Python</div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">AST & Güvenlik</div>
                </div>
                <div style="background: #1F2937; border: 1px solid rgba(255, 255, 255, 0.06); padding: 1.2rem 1rem; border-radius: 12px; width: 160px; text-align: center;">
                    <div style="font-size: 1.6rem;">⚡</div>
                    <div style="font-weight: 600; color: #F1F5F9; margin-top: 6px; font-size: 0.95rem;">C / C++</div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">Bellek & Sızıntı</div>
                </div>
                <div style="background: #1F2937; border: 1px solid rgba(255, 255, 255, 0.06); padding: 1.2rem 1rem; border-radius: 12px; width: 160px; text-align: center;">
                    <div style="font-size: 1.6rem;">☕</div>
                    <div style="font-weight: 600; color: #F1F5F9; margin-top: 6px; font-size: 0.95rem;">Java</div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">SQLi & Enjeksiyon</div>
                </div>
                <div style="background: #1F2937; border: 1px solid rgba(255, 255, 255, 0.06); padding: 1.2rem 1rem; border-radius: 12px; width: 160px; text-align: center;">
                    <div style="font-size: 1.6rem;">🤖</div>
                    <div style="font-weight: 600; color: #F1F5F9; margin-top: 6px; font-size: 0.95rem;">Qwen AI</div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">Derin Kod Analizi</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


