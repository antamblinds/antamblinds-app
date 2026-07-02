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
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - HỆ THỐNG CLOUD")

# Lấy bí mật và TỰ ĐỘNG LÀM SẠCH ID (Xóa dấu chấm, khoảng trắng dư)
api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
drive_json = st.secrets.get("GOOGLE_DRIVE_JSON")
f_measure = st.secrets.get("FOLDER_MEASUREMENTS", "").strip().strip('.')
f_invoice = st.secrets.get("FOLDER_INVOICES", "").strip().strip('.')

def upload_to_drive(content, name, mime, folder):
    if not folder:
        st.error("Ông chưa dán ID Folder vào Secrets kìa!")
        return False
    try:
        info = json.loads(drive_json)
        creds = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {'name': name, 'parents': [folder]}
        media = MediaIoBaseUpload(BytesIO(content), mimetype=mime, resumable=True)
        service.files().create(body=file_metadata, media_body=media).execute()
        return True
    except Exception as e:
        # Hiện lỗi rõ ràng để ông biết do ID hay do chưa Share
        st.error(f"LỖI DRIVE: {e}")
        st.info(f"Mẹo: Hãy đảm bảo đã Share folder ID '{folder}' cho email: {info.get('client_email')}")
        return False

# 2. CHẠY AI VÀ MENU
if api_key:
    try:
        genai.configure(api_key=api_key)
        # Lấy model đang chạy tốt cho ông nãy giờ
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        m_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else models[0]
        model = genai.GenerativeModel(m_name)

        st.sidebar.title("DANH MỤC")
        task = st.sidebar.radio("CHỌN VIỆC:", ["Ghi Sổ Đo -> Cloud", "Lưu Invoice -> Cloud"])
        unit_price = st.sidebar.number_input("Giá ($/m2):", value=100.0)

        if task == "Ghi Sổ Đo -> Cloud":
            img_file = st.camera_input("CHỤP SỔ ĐO")
            if img_file:
                with st.spinner('Đang đọc và gửi lên Drive...'):
                    img = PIL.Image.open(img_file)
                    res = model.generate_content(["Read. Format: ADDRESS: [addr] DATA: [Location|Width/Height]", img])
                    st.info(res.text)
                    
                    # Tạo Excel
                    out = BytesIO()
                    df = pd.DataFrame([{"NoiDung": res.text}])
                    with pd.ExcelWriter(out, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    
                    # GỬI LÊN DRIVE
                    if upload_to_drive(out.getvalue(), "So_Do_An_Tam.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", f_measure):
                        st.success("🚀 QUÁ NGON! ĐÃ VÀO DRIVE!")

        else: # INVOICE
            inv_file = st.camera_input("CHỤP INVOICE")
            if inv_file:
                with st.spinner('Đang gửi Invoice...'):
                    pdf = FPDF()
                    pdf.add_page()
                    img_inv = PIL.Image.open(inv_file)
                    pdf.image(img_inv, x=10, y=10, w=190)
                    if upload_to_drive(bytes(pdf.output()), "Invoice_AnTam.pdf", "application/pdf", f_invoice):
                        st.success("✅ INVOICE ĐÃ LƯU!")
    except Exception as e:
        st.error(f"Lỗi AI: {e}")
