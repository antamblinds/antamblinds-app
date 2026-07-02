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

# 1. CẤU HÌNH HUB
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - HỆ THỐNG CLOUD")

# Lấy thông tin từ Secrets
api_key = st.secrets.get("GEMINI_API_KEY")
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
        model = genai.GenerativeModel('gemini-1.5-flash')

        st.sidebar.title("MENU QUẢN LÝ")
        task = st.sidebar.radio("CHỌN VIỆC:", ["Ghi Sổ Đo -> Cloud", "Lưu Invoice -> Cloud"])
        unit_price = st.sidebar.number_input("Giá ($$/m2):", value=100.0)

        if task == "Ghi Sổ Đo -> Cloud":
            uploaded_file = st.camera_input("CHỤP SỔ ĐO")
            if uploaded_file:
                with st.spinner('Đang đọc và gửi lên Drive...'):
                    img = PIL.Image.open(uploaded_file)
                    prompt = "Find ADDRESS. List items: [Location] | [Width/Height]. Format: ADDRESS: [address] DATA: [items]"
                    response = model.generate_content([prompt, img])
                    
                    address_found = "DonHang_Moi"
                    data_rows = []
                    # Tách lấy số và địa chỉ
                    lines = response.text.strip().split('\n')
                    for line in lines:
                        if "ADDRESS:" in line: address_found = line.split("ADDRESS:")[1].strip()
                        elif "|" in line:
                            parts = line.split("|")
                            if len(parts) >= 2:
                                match = re.search(r"(\d+)/(\d+)", parts[1])
                                if match:
                                    w, h = float(match.group(1).strip()), float(match.group(2).strip())
                                    area = max((w * h) / 1000000, 1.5)
                                    data_rows.append({"Vị trí": parts[0].strip(), "Kích thước": parts[1].strip(), "M2 tính tiền": round(area, 2), "Tiền ($$)": round(area * unit_price, 2)})
                    
                    if data_rows:
                        df = pd.DataFrame(data_rows)
                        st.table(df)
                        # Tạo file Excel
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        filename = f"{address_found.replace(' ', '_')}.xlsx"
                        # Gửi lên Drive
                        if upload_to_drive(output.getvalue(), filename, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", folder_measure):
                            st.success(f"🚀 XONG RỒI! ĐÃ VÀO DRIVE: {filename}")
        
        else: # Phần chụp Invoice
            invoice_file = st.camera_input("CHỤP INVOICE")
            if invoice_file:
                with st.spinner('Đang chuyển thành PDF và gửi đi...'):
                    pdf = FPDF()
                    pdf.add_page()
                    img_inv = PIL.Image.open(invoice_file)
                    pdf.image(img_inv, x=10, y=10, w=190)
                    pdf_bytes = bytes(pdf.output())
                    
                    if upload_to_drive(pdf_bytes, "Invoice_AnTam_Moi.pdf", "application/pdf", folder_invoice):
                        st.success("✅ INVOICE ĐÃ ĐƯỢC LƯU VÀO DRIVE!")

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
else:
    st.warning("Dán cái mã AQ hồi nãy vào Secrets nha Jimmy!")
