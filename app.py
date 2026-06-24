import streamlit as st
import anthropic
import fitz  # pymupdf
import docx
import json
import re
import io

st.set_page_config(page_title="Recruiter Assistant", page_icon="🔍", layout="wide")

st.title("🔍 Recruiter Assistant")
st.caption("Upload a Job Description and multiple CVs — get AI-powered candidate rankings instantly")

# ── API Key ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        st.success("API key loaded from secrets ✓")
    except Exception:
        api_key = st.text_input("Anthropic API Key", type="password",
                                help="Get yours at console.anthropic.com")

if not api_key:
    st.warning("👈 Enter your Anthropic API key in the sidebar to get started.")
    st.stop()

# ── Helper functions ─────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
    return "".join(page.get_text() for page in pdf_doc)

def extract_text_from_docx(file_bytes: bytes) -> str:
    document = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())

def clean_and_parse_json(text: str) -> dict:
    text = re.sub(r"```json|```", "", text).strip()
    return json.loads(text)

def analyze_candidate(claude_client, jd_text: str, cv_text: str, filename: str) -> dict:
    prompt = (
        'Return ONLY raw JSON, no markdown, no explanation:\n'
        '{"name": "candidate full name from CV", "overall_score": 7, '
        '"technical": 6, "experience": 7, "education": 5, "soft_skills": 8, '
        '"top_strength": "one sentence", "top_gap": "one sentence", '
        '"recommendation": "hire/maybe/pass"}\n\n'
        f"JD:\n{jd_text[:2000]}\n\nCV:\n{cv_text[:2000]}"
    )
    response = claude_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    result = clean_and_parse_json(response.content[0].text)
    result["filename"] = filename
    return result

# ── Upload section ───────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Job Description")
    jd_file = st.file_uploader("Upload JD (PDF)", type=["pdf"])

with col2:
    st.subheader("📄 Candidate CVs")
    cv_files = st.file_uploader(
        "Upload CVs (PDF or DOCX) — select multiple",
        type=["pdf", "docx"],
        accept_multiple_files=True,
    )

# ── Analyse button ───────────────────────────────────────────────────────────
if jd_file and cv_files:
    if st.button("🚀 Analyse Candidates", type="primary", use_container_width=True):
        jd_bytes = jd_file.read()
        jd_text = extract_text_from_pdf(jd_bytes)

        if not jd_text.strip():
            st.error("Could not extract text from the JD PDF — make sure it is not a scanned image.")
            st.stop()

        claude = anthropic.Anthropic(api_key=api_key)
        results = []
        progress_bar = st.progress(0)
        status = st.empty()

        for i, cv_file in enumerate(cv_files):
            status.text(f"Analysing {cv_file.name} …")
            progress_bar.progress((i + 1) / len(cv_files))

            try:
                file_bytes = cv_file.read()
                if cv_file.name.lower().endswith(".pdf"):
                    cv_text = extract_text_from_pdf(file_bytes)
                else:
                    cv_text = extract_text_from_docx(file_bytes)

                if len(cv_text) < 100:
                    st.warning(f"Skipping {cv_file.name} — too little text could be extracted.")
                    continue

                result = analyze_candidate(claude, jd_text, cv_text, cv_file.name)
                results.append(result)

            except Exception as e:
                st.warning(f"Could not process {cv_file.name}: {e}")

        progress_bar.empty()
        status.empty()

        if not results:
            st.error("No candidates could be analysed. Check your CV files.")
            st.stop()

        results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        st.markdown("---")
        st.subheader(f"📊 Results — {len(results)} candidate(s) ranked")

        REC_ICON = {"hire": "🟢", "maybe": "🟡", "pass": "🔴"}

        for i, r in enumerate(results, 1):
            rec = r.get("recommendation", "pass").lower()
            icon = REC_ICON.get(rec, "⚪")
            score = r.get("overall_score", 0)
            name = r.get("name", "Candidate")

            with st.expander(
                f"{icon}  #{i} — {name} | {score}/10 | {rec.upper()}",
                expanded=(i == 1),
            ):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Technical", f"{r.get('technical', 0)}/10")
                c2.metric("Experience", f"{r.get('experience', 0)}/10")
                c3.metric("Education", f"{r.get('education', 0)}/10")
                c4.metric("Soft Skills", f"{r.get('soft_skills', 0)}/10")
                st.write(f"**✅ Top Strength:** {r.get('top_strength', '—')}")
                st.write(f"**⚠️ Top Gap:** {r.get('top_gap', '—')}")
                st.caption(f"File: {r.get('filename', '')}")

elif not jd_file:
    st.info("👆 Start by uploading a Job Description PDF.")
elif not cv_files:
    st.info("👆 Now upload one or more CV files (PDF or DOCX).")
