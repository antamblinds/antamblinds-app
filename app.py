import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
import json
from io import BytesIO
from fpdf import FPDF
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. CẤU HÌNH
st.set_page_config(page_title="An Tam Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - AUTO SYSTEM")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
drive_json = st.secrets.get("GOOGLE_DRIVE_JSON")
f_measure = st.secrets.get("FOLDER_MEASUREMENTS", "").strip().strip('.')

def upload_to_drive(content, name, mime, folder):
    try:
        info = json.loads(drive_json)
        creds = service_account.Credentials.from_service_account_info(info).with_scopes(['https://www.googleapis.com/auth/drive'])
        service = build('drive', 'v3', credentials=creds)
        meta = {'name': name, 'parents': [folder]}
        media = MediaIoBaseUpload(BytesIO(content), mimetype=mime, resumable=False)
        service.files().create(body=meta, media_body=media).execute()
        return True
    except: return False

# 2. CHẠY AI
if api_key:
    genai.configure(api_key=api_key)
    # Lấy model đang chạy tốt cho ông
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    m_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else models[0]
    model = genai.GenerativeModel(m_name)

    st.sidebar.title("MENU")
    task = st.sidebar.radio("CHỌN VIỆC:", ["Ghi Sổ Đo -> Cloud", "Lưu Invoice -> Cloud"])
    
    if task == "Ghi Sổ Đo -> Cloud":
        img_f = st.camera_input("CHỤP SỔ ĐO")
        if img_f:
            with st.spinner('AI đang đọc...'):
                try:
                    img = PIL.Image.open(img_f)
                    res = model.generate_content(["Read address and measurements. Format: ADDRESS: [addr] DATA: [Location|W/H]", img])
                    st.info(res.text)
                    
                    # Tạo file Excel
                    out = BytesIO()
                    pd.DataFrame([{"Content": res.text}]).to_excel(out, index=False)
                    excel_data = out.getvalue()
                    
                    # NÚT THOÁT HIỂM: TẢI VỀ MÁY NGAY!
                    st.download_button("📥 NHẤN VÀO ĐÂY ĐỂ TẢI EXCEL VỀ MÁY", excel_data, "SoDo_AnTam.xlsx")
                    
                    # Thử gửi Drive
                    if upload_to_drive(excel_data, "SoDo_AnTam.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", f_measure):
                        st.success("✅ ĐÃ TỰ ĐỘNG LƯU VÀO DRIVE!")
                except Exception as e:
                    if "429" in str(e): st.error("AI mệt rồi, ông đợi 30 giây nữa hãy chụp lại nhé!")
                    else: st.error(f"Lỗi: {e}")
