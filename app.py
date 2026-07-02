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

# 1. CẤU HÌNH HUB
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - QUẢN LÝ AUTO")

# Lấy thông tin bí mật
api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
drive_json = st.secrets.get("GOOGLE_DRIVE_JSON")
f_measure = st.secrets.get("FOLDER_MEASUREMENTS", "").strip().strip('.')
f_invoice = st.secrets.get("FOLDER_INVOICES", "").strip().strip('.')

# HÀM DRIVE (Sửa lỗi 403)
def upload_to_drive(content, name, mime, folder):
    try:
        info = json.loads(drive_json)
        creds = service_account.Credentials.from_service_account_info(info).with_scopes(['https://www.googleapis.com/auth/drive'])
        service = build('drive', 'v3', credentials=creds)
        
        meta = {'name': name, 'parents': [folder]}
        # Tắt resumable=True để tránh lỗi dung lượng cho robot
        media = MediaIoBaseUpload(BytesIO(content), mimetype=mime, resumable=False)
        service.files().create(body=meta, media_body=media).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi Drive (Google chặn robot): {e}")
        return False

# 2. CHẠY AI VÀ MENU
if api_key:
    try:
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        m_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else models[0]
        model = genai.GenerativeModel(m_name)

        st.sidebar.title("DANH MỤC")
        task = st.sidebar.radio("CHỌN VIỆC:", ["Ghi Sổ Đo -> Cloud", "Lưu Invoice -> Cloud"])
        unit_price = st.sidebar.number_input("Giá ($/m2):", value=100.0)

        if task == "Ghi Sổ Đo -> Cloud":
            img_f = st.camera_input("CHỤP SỔ ĐO")
            if img_f:
                with st.spinner('AI đang làm việc...'):
                    img = PIL.Image.open(img_f)
                    res = model.generate_content(["Read address and measurements. Format: ADDRESS: [addr] DATA: [Location|W/H]", img])
                    st.info(res.text)
                    
                    # TẠO FILE EXCEL
                    out = BytesIO()
                    pd.DataFrame([{"Data": res.text}]).to_excel(out, index=False)
                    excel_data = out.getvalue()
                    
                    # 1. HIỆN NÚT TẢI VỀ MÁY NGAY (CHO CHẮC ĂN)
                    st.download_button("📥 TẢI EXCEL VỀ MÁY", excel_data, "SoDo_AnTam.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    
                    # 2. THỬ GỬI DRIVE
                    if upload_to_drive(excel_data, "SoDo_AnTam.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", f_measure):
                        st.success("✅ ĐÃ TỰ ĐỘNG LƯU VÀO DRIVE!")

        else: # LƯU INVOICE
            inv_f = st.camera_input("CHỤP INVOICE")
            if inv_f:
                with st.spinner('Đang tạo PDF...'):
                    pdf = FPDF()
                    pdf.add_page()
                    img_inv = PIL.Image.open(inv_f)
                    pdf.image(img_inv, x=10, y=10, w=190)
                    pdf_data = bytes(pdf.output())
                    
                    # 1. NÚT TẢI VỀ MÁY
                    st.download_button("📥 TẢI INVOICE PDF", pdf_data, "Invoice_AnTam.pdf", "application/pdf")
                    
                    # 2. THỬ GỬI DRIVE
                    if upload_to_drive(pdf_data, "Invoice_AnTam.pdf", "application/pdf", f_invoice):
                        st.success("✅ INVOICE ĐÃ LƯU VÀO DRIVE!")
    except Exception as e:
        st.error(f"Lỗi AI: {e}")
