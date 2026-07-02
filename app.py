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

# Lấy thông tin (Sửa lỗi lấy Key bị dư khoảng trắng)
api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
drive_json = st.secrets.get("GOOGLE_DRIVE_JSON")
folder_measure = st.secrets.get("FOLDER_MEASUREMENTS")
folder_invoice = st.secrets.get("FOLDER_INVOCES")

# Hàm gửi Drive
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

# 2. CHƯƠNG TRÌNH CHÍNH
if api_key:
    try:
        # Cấu hình với mã AQ của Jimmy
        genai.configure(api_key=api_key)
        
        # THAY ĐỔI QUAN TRỌNG: Thêm bản 'latest' để sửa lỗi 404
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        st.sidebar.title("MENU")
        task = st.sidebar.radio("CHỌN VIỆC:", ["Ghi Sổ Đo -> Cloud", "Lưu Invoice -> Cloud"])
        unit_price = st.sidebar.number_input("Giá ($/m2):", value=100.0)

        if task == "Ghi Sổ Đo -> Cloud":
            uploaded_file = st.camera_input("CHỤP SỔ ĐO")
            if uploaded_file:
                with st.spinner('AI đang đọc số đo...'):
                    img = PIL.Image.open(uploaded_file)
                    # Ra lệnh đơn giản nhất cho AI
                    prompt = "Find ADDRESS. List items: [Location] | [Width/Height]. Format: ADDRESS: [address] DATA: [items]"
                    response = model.generate_content([prompt, img])
                    
                    st.write("### Kết quả:")
                    st.info(response.text)
                    
                    # Tạo Excel và gửi Drive
                    output = BytesIO()
                    df = pd.DataFrame([{"Content": response.text}])
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    
                    if upload_to_drive(output.getvalue(), "Don_Hang_Moi.xlsx", folder_measure):
                        st.success("✅ ĐÃ GỬI LÊN DRIVE THÀNH CÔNG!")
        
        else: # Invoice
            invoice_file = st.camera_input("CHỤP INVOICE")
            if invoice_file:
                with st.spinner('Đang gửi...'):
                    pdf = FPDF()
                    pdf.add_page()
                    img_inv = PIL.Image.open(invoice_file)
                    pdf.image(img_inv, x=10, y=10, w=190)
                    if upload_to_drive(bytes(pdf.output()), "Invoice_Moi.pdf", "application/pdf", folder_invoice):
                        st.success("✅ ĐÃ LƯU INVOICE!")

    except Exception as e:
        st.error(f"Vẫn còn lỗi AI: {e}. Jimmy kiểm tra lại xem đã bấm ENABLE Generative Language API bên Google Cloud chưa nhé!")
else:
    st.error("Chưa thấy mã AQ trong Secrets!")
