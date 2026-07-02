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

# 1. LẤY THÔNG TIN TỪ SECRETS
api_key = st.secrets.get("GEMINI_API_KEY")
drive_json = st.secrets.get("GOOGLE_DRIVE_JSON")
folder_measure = st.secrets.get("FOLDER_MEASUREMENTS")
folder_invoice = st.secrets.get("FOLDER_INVOICES")

st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - CÔNG CỤ TỰ ĐỘNG")

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

# Hàm tạo PDF cho Invoice
def export_as_pdf(image_file):
    pdf = FPDF()
    pdf.add_page()
    img = PIL.Image.open(image_file)
    pdf.image(img, x=10, y=10, w=190)
    return bytes(pdf.output())

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Sửa tên model về bản gốc chuẩn nhất
        model = genai.GenerativeModel('gemini-1.5-flash')

        st.sidebar.title("DANH MỤC")
        task = st.sidebar.radio("CHỌN LOẠI CÔNG VIỆC:", ["Ghi Sổ Đo -> Cloud", "Lưu Invoice -> Cloud"])
        unit_price = st.sidebar.number_input("Đơn giá ($$/m2):", value=100.0)

        if task == "Ghi Sổ Đo -> Cloud":
            uploaded_file = st.camera_input("CHỤP SỔ ĐO")
            if uploaded_file:
                with st.spinner('Đang đọc và gửi đi...'):
                    img = PIL.Image.open(uploaded_file)
                    prompt = "Read image accurately. Find ADDRESS. List items: [Location] | [Width/Height.lkc]. Format: ADDRESS: [address] DATA: [items]"
                    response = model.generate_content([prompt, img])
                    text_data = response.text
                    
                    address_found = "DonHang_Moi"
                    data_rows = []
                    lines = text_data.strip().split('\n')
                    for line in lines:
                        if "ADDRESS:" in line: address_found = line.split("ADDRESS:")[1].strip()
                        elif "|" in line:
                            parts = line.split("|")
                            if len(parts) >= 2:
                                match = re.search(r"(\d+)/(\d+)", parts[1])
                                if match:
                                    w, h = float(match.group(1).strip()), float(match.group(2).strip())
                                    area = max((w * h) / 1000000, 1.5)
                                    data_rows.append({"Vị trí": parts[0].strip(), "Kích thước (.lkc)": parts[1].strip(), "M2 tính tiền": round(area, 2), "Thành tiền ($$)": round(area * unit_price, 2)})
                    
                    if data_rows:
                        df = pd.DataFrame(data_rows)
                        st.table(df)
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        xls_filename = f"{address_found.replace(' ', '_')}.xlsx"
                        if upload_to_drive(output.getvalue(), xls_filename, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", folder_measure):
                            st.success(f"✅ Đã vào Drive: {xls_filename}")
        
        else: # Phần Invoice
            invoice_file = st.camera_input("CHỤP INVOICE")
            if invoice_file:
                with st.spinner('Đang gửi lên Cloud...'):
                    pdf_bytes = export_as_pdf(invoice_file)
                    if upload_to_drive(pdf_bytes, "Invoice_AnTam_Moi.pdf", "application/pdf", folder_invoice):
                        st.success("✅ Đã lưu Invoice vào Drive!")

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
else:
    st.warning("Thiếu API Key kìa Jimmy ơi!")
