import streamlit as st
import whisper
from docx import Document
import tempfile
import os

# ---------------------- 工具函數 ----------------------
def seconds_to_hms(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

@st.cache_resource
def load_whisper_model(model_name: str):
    """快取模型，避免每次重新載入"""
    return whisper.load_model(model_name)

# ---------------------- 頁面設定 ----------------------
st.set_page_config(
    page_title="MP3語音轉Word(含時間軸)",
    page_icon="🎙️",
    layout="wide"
)
st.title("🎙️ MP3 語音轉文字｜自動帶時間軸 + 標點｜匯出Word")
st.markdown("支援中文，轉寫完成後可下載docx檔")

# ---------------------- 側邊欄設定 ----------------------
with st.sidebar:
    st.header("參數設定")
    model_option = st.selectbox(
        "Whisper模型（越大越準、越吃記憶體）",
        ["base", "small", "tiny"],
        index=0
    )
    st.info("建議線上免費環境優先使用 base，small 在 Streamlit Cloud 容易記憶體不足失敗")

# ---------------------- 檔案上傳 ----------------------
uploaded_file = st.file_uploader("請上傳 MP3 音檔", type=["mp3"])

if uploaded_file is not None:
    st.success(f"✅ 已上傳檔案：{uploaded_file.name}")

    # 建立暫存檔案（whisper需要本地檔案路徑讀取）
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
        tmp_audio.write(uploaded_file.read())
        tmp_audio_path = tmp_audio.name

    # 載入模型
    with st.spinner("正在載入Whisper模型..."):
        model = load_whisper_model(model_option)

    # 開始轉寫
    if st.button("開始語音辨識轉寫"):
        with st.spinner("辨識中，請等候...（音檔越久等待越久）"):
            result = model.transcribe(
                tmp_audio_path,
                language="zh",
                word_timestamps=True
            )

        # 建立Word
        doc = Document()
        doc.add_heading("MP3語音轉文字（含時間軸）", level=1)
        output_text_list = []

        for seg in result["segments"]:
            start_str = seconds_to_hms(seg["start"])
            end_str = seconds_to_hms(seg["end"])
            seg_text = seg["text"].strip()
            line = f"[{start_str} → {end_str}] {seg_text}"
            output_text_list.append(line)
            doc.add_paragraph(line)

        # 把word存到暫存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_doc:
            doc.save(tmp_doc)
            tmp_doc_path = tmp_doc.name

        # 顯示預覽
        st.subheader("📄 轉寫預覽")
        preview_text = "\n".join(output_text_list)
        st.text_area("轉寫內容", preview_text, height=400)

        # 下載按鈕
        with open(tmp_doc_path, "rb") as f:
            st.download_button(
                label="📥 下載 Word (.docx)",
                data=f,
                file_name=f"{uploaded_file.name}_轉寫結果.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        # 清理暫存檔
        os.unlink(tmp_audio_path)
        os.unlink(tmp_doc_path)

else:
    st.info("👆 請先在上方選擇一個MP3檔案上傳")
