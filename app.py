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
st.header("🏠 AN TAM BLINDS - HỆ THỐNG CLOUD")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
drive_json = st.secrets.get("GOOGLE_DRIVE_JSON")
f_measure = st.secrets.get("FOLDER_MEASUREMENTS", "").strip()
f_invoice = st.secrets.get("FOLDER_INVOICES", "").strip()

def upload_to_drive(content, name, mime, folder):
    try:
        info = json.loads(drive_json)
        # Mở quyền Drive
        creds = service_account.Credentials.from_service_account_info(info).with_scopes(['https://www.googleapis.com/auth/drive'])
        service = build('drive', 'v3', credentials=creds)
        
        meta = {'name': name, 'parents': [folder]}
        media = MediaIoBaseUpload(BytesIO(content), mimetype=mime, resumable=True)
        service.files().create(body=meta, media_body=media).execute()
        return True
    except Exception as e:
        st.error(f"⚠️ LỖI DRIVE: {e}")
        st.info("Kiểm tra xem đã Share thư mục CHA cho robot chưa ông nhé!")
        return False

# 2. MENU VÀ AI
if api_key:
    genai.configure(api_key=api_key)
    # Lấy model AI (Bản sửa lỗi cho mã AQ)
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    m_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else models[0]
    model = genai.GenerativeModel(m_name)

    st.sidebar.title("DANH MỤC")
    task = st.sidebar.radio("CHỌN VIỆC:", ["Ghi Sổ Đo -> Cloud", "Lưu Invoice -> Cloud"])
    
    if task == "Ghi Sổ Đo -> Cloud":
        img_f = st.camera_input("CHỤP SỔ ĐO")
        if img_f:
            with st.spinner('Đang làm việc...'):
                img = PIL.Image.open(img_f)
                res = model.generate_content(["Read address and sizes. Format: ADDRESS: [addr] DATA: [Location|W/H]", img])
                st.info(res.text)
                # Xuất file Excel
                out = BytesIO()
                pd.DataFrame([{"Data": res.text}]).to_excel(out, index=False)
                if upload_to_drive(out.getvalue(), "SoDo_AnTam.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", f_measure):
                    st.success("✅ ĐÃ LƯU VÀO DRIVE!")

    else: # INVOICE
        inv_f = st.camera_input("CHỤP INVOICE")
        if inv_f:
            with st.spinner('Đang gửi...'):
                pdf = FPDF()
                pdf.add_page()
                img_inv = PIL.Image.open(inv_f)
                pdf.image(img_inv, x=10, y=10, w=190)
                if upload_to_drive(bytes(pdf.output()), "Invoice_AnTam.pdf", "application/pdf", f_invoice):
                    st.success("✅ INVOICE ĐÃ LƯU!")
