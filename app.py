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

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - HỆ THỐNG TỰ ĐỘNG")

# Lấy bí mật từ Secrets
api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
drive_json = st.secrets.get("GOOGLE_DRIVE_JSON")
f_measure = st.secrets.get("FOLDER_MEASUREMENTS", "").strip().strip('.')
f_invoice = st.secrets.get("FOLDER_INVOICES", "").strip().strip('.')

# HÀM DRIVE (Đã sửa lỗi quyền truy cập)
def upload_to_drive(content, name, mime, folder):
    try:
        info = json.loads(drive_json)
        # THÊM DÒNG NÀY ĐỂ MỞ CỬA DRIVE:
        scopes = ['https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_info(info).with_scopes(scopes)
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {'name': name, 'parents': [folder]}
        media = MediaIoBaseUpload(BytesIO(content), mimetype=mime, resumable=True)
        service.files().create(body=file_metadata, media_body=media).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi Drive: {e}")
        return False

# 2. CHẠY AI VÀ MENU
if api_key:
    try:
        genai.configure(api_key=api_key)
        # Tự động lấy model AI
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        m_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else models[0]
        model = genai.GenerativeModel(m_name)

        # MENU ĐÃ QUAY TRỞ LẠI
        st.sidebar.title("DANH MỤC")
        task = st.sidebar.radio("CHỌN VIỆC:", ["Ghi Sổ Đo -> Cloud", "Lưu Invoice -> Cloud"])
        unit_price = st.sidebar.number_input("Giá ($/m2):", value=100.0)

        if task == "Ghi Sổ Đo -> Cloud":
            img_file = st.camera_input("CHỤP SỔ ĐO")
            if img_file:
                with st.spinner('Đang đọc và gửi lên Drive...'):
                    img = PIL.Image.open(img_file)
                    res = model.generate_content(["Read address and sizes. Format: ADDRESS: [addr] DATA: [Location|W/H]", img])
                    st.info(res.text)
                    
                    # Tạo Excel
                    out = BytesIO()
                    df = pd.DataFrame([{"NoiDung": res.text}])
                    with pd.ExcelWriter(out, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    
                    if upload_to_drive(out.getvalue(), "So_Do_An_Tam.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", f_measure):
                        st.success("🚀 XONG RỒI JIMMY! FILE ĐÃ VÀO DRIVE!")

        else: # PHẦN INVOICE
            inv_file = st.camera_input("CHỤP INVOICE")
            if inv_file:
                with st.spinner('Đang gửi Invoice...'):
                    pdf = FPDF()
                    pdf.add_page()
                    img_inv = PIL.Image.open(inv_file)
                    pdf.image(img_inv, x=10, y=10, w=190)
                    if upload_to_drive(bytes(pdf.output()), "Invoice_AnTam.pdf", "application/pdf", f_invoice):
                        st.success("✅ INVOICE ĐÃ LƯU VÀO DRIVE!")
    except Exception as e:
        st.error(f"Lỗi AI: {e}")
else:
    st.error("Dán mã API vào Secrets đi Jimmy!")
