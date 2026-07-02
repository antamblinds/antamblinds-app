import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from fpdf import FPDF
from io import BytesIO
import re
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. CẤU HÌNH HỆ THỐNG
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - QUẢN LÝ CLOUD")

# Lấy thông tin từ Secrets
raw_api_key = st.secrets.get("GEMINI_API_KEY", "")
api_key = raw_api_key.strip() # Xóa khoảng trắng dư thừa
drive_json = st.secrets.get("GOOGLE_DRIVE_JSON")
folder_measure = st.secrets.get("FOLDER_MEASUREMENTS")
folder_invoice = st.secrets.get("FOLDER_INVOICES")

# Hàm gửi file lên Drive
def upload_to_drive(file_content, file_name, mime_type, target_folder):
    try:
        info = json.loads(drive_json)
        creds = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': file_name, 'parents': [target_folder]}
        media = MediaIoBaseUpload(BytesIO(file_content), mimetype=mime_type, resumable=True)
        service.files().create(body=file_metadata, media_body=media).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi Drive: {e}")
        return False

# 2. XỬ LÝ CHÍNH
if api_key:
    try:
        # Cấu hình AI với mã AQ của Jimmy
        genai.configure(api_key=api_key)
        # Sửa lỗi 404: Dùng tên model chuẩn nhất cho mã AQ
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')

        st.sidebar.title("DANH MỤC")
        task = st.sidebar.radio("CHỌN VIỆC:", ["Ghi Sổ Đo -> Cloud", "Lưu Invoice -> Cloud"])
        unit_price = st.sidebar.number_input("Giá ($/m2):", value=100.0)

        if task == "Ghi Sổ Đo -> Cloud":
            uploaded_file = st.camera_input("CHỤP SỔ ĐO")
            if uploaded_file:
                with st.spinner('AI đang đọc số đo...'):
                    img = PIL.Image.open(uploaded_file)
                    # Lệnh AI đơn giản nhất để tránh lỗi
                    prompt = "Find ADDRESS. List items: [Location] | [Width/Height]. Format: ADDRESS: [address] DATA: [items]"
                    response = model.generate_content([prompt, img])
                    
                    st.write("### Kết quả đọc được:")
                    st.info(response.text)
                    
                    # Tạo Excel và gửi Drive
                    output = BytesIO()
                    df = pd.DataFrame([{"Content": response.text}])
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    
                    if upload_to_drive(output.getvalue(), "So_Do_An_Tam.xlsx", folder_measure):
                        st.success("✅ QUÁ NGON! FILE ĐÃ VÀO DRIVE!")
        
        else: # Phần chụp Invoice
            invoice_file = st.camera_input("CHỤP INVOICE")
            if invoice_file:
                with st.spinner('Đang lưu...'):
                    pdf = FPDF()
                    pdf.add_page()
                    img_inv = PIL.Image.open(invoice_file)
                    pdf.image(img_inv, x=10, y=10, w=190)
                    if upload_to_drive(bytes(pdf.output()), "Invoice_Moi.pdf", "application/pdf", folder_invoice):
                        st.success("✅ ĐÃ LƯU INVOICE!")

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
else:
    st.error("Dán chìa khóa AQ trên vào Secrets nha Jimmy!")
