import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH HUB
st.set_page_config(page_title="An Tam Blinds Tool", layout="wide")
st.header("🏠 AN TAM BLINDS - CÔNG CỤ SỔ ĐO & INVOICE")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

# Khởi tạo bộ nhớ tạm để tránh lỗi 429
if 'results' not in st.session_state: st.session_state.results = None
if 'address' not in st.session_state: st.session_state.address = "Khach_Hang"

if api_key:
    genai.configure(api_key=api_key)
    # Tự động chọn model AI
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(models[0])

    # MENU ĐƠN GIẢN
    st.sidebar.title("CÔNG VIỆC")
    task = st.sidebar.radio("CHỌN LOẠI:", ["📝 Ghi Sổ Đo -> Excel", "🧾 Lưu Invoice -> PDF"])

    # --- PHẦN 1: GHI SỔ ĐO ---
    if task == "📝 Ghi Sổ Đo -> Excel":
        st.subheader("📝 CHỤP SỔ ĐO (Tự động chuyển Excel)")
        img_file = st.camera_input("CHỤP TỜ GIẤY ĐO")
        
        if img_file:
            if st.button("🚀 XÁC NHẬN ĐỌC SỐ ĐO"):
                with st.spinner('AI đang bóc tách số liệu...'):
                    try:
                        img = PIL.Image.open(img_file)
                        # Prompt tối giản để lấy đúng số
                        prompt = "Read client address and measurements. Format: ADDRESS: [addr] DATA: [Location | Width | Height]"
                        res = model.generate_content([prompt, img])
                        st.session_state.results = res.text
                    except Exception as e:
                        
