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

# --- 1. LẤY "CHÌA KHÓA" TỪ PHẦN SECRETS ÔNG VỪA DÁN ---
api_key = st.secrets.get("GEMINI_API_KEY")
drive_json = st.secrets.get("GOOGLE_DRIVE_JSON")
folder_measure = st.secrets.get("FOLDER_MEASUREMENTS")
folder_invoice = st.secrets.get("FOLDER_INVOICES")

st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - TỰ ĐỘNG HÓA CLOUD")

# --- 2. HÀM GỬI FILE LÊN GOOGLE DRIVE (Cái này quan trọng nhất) ---
def upload_to_drive(file_content, file_name, mime_type, target_folder):
    try:
        # Giải mã cái mớ JSON trong Secrets
        info = json.loads(drive_json)
        creds = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=creds)
        
        # Tạo thông tin file và chỉ định nó vào folder nào
        file_metadata = {'name': file_name, 'parents': [target_folder]}
        media = MediaIoBaseUpload(BytesIO(file_content), mimetype=mime_type, resumable=True)
        
        # Thực hiện lệnh upload
        service.files().create(body=file_metadata, media_body=media).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi Drive: {e}")
        return False

# --- 3. HÀM TẠO PDF TỪ ẢNH (Dùng cho Invoice) ---
def export_as_pdf(image_file):
    pdf = FPDF()
    pdf.add_page()
    img = PIL.Image.open(image_file)
    pdf.image(img, x=10, y=10, w=190)
    return bytes(pdf.output())

# --- 4. CHƯƠNG TRÌNH CHÍNH ---
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-1.5-flash')

    st.sidebar.title("DANH MỤC")
    task = st.sidebar.radio("CHỌN LOẠI CÔNG VIỆC:", ["Ghi Sổ Đo -> Cloud", "Lưu Invoice -> Cloud"])
    unit_price = st.sidebar.number_input("Đơn giá ($$/m2):", value=100.0)

    # A. PHẦN XỬ LÝ SỔ ĐO
    if task == "Ghi Sổ Đo -> Cloud":
        uploaded_file = st.camera_input("CHỤP SỔ ĐO")
        if uploaded_file:
            with st.spinner('AI đang đọc và gửi đi...'):
                img = PIL.Image.open(uploaded_file)
                prompt = "Read image accurately. Find ADDRESS. List items: [Location] | [Width/Height.lkc]. Format: ADDRESS: [address] \n DATA: [items]"
                response = model.generate_content([prompt, img])
                text_data = response.text
                
                address_found = "DonHang_Moi"
                data_rows = []
                lines = text_data.strip().split('\n')
                for line in lines:
                    if "ADDRESS:" in line:
                        address_found = line.split("ADDRESS:")[1].strip()
                    elif "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 2:
                            match = re.search(r"(\d+)/(\d+)", parts[1])
                            if match:
                                w, h = float(match.group(1).strip()), float(match.group(2).strip())
                                area = max((w * h) / 1000000, 1.5)
                                data_rows.append({
                                    "Vị trí": parts[0].strip(),
                                    "Kích thước (.lkc)": parts[1].strip(),
                                    "M2 thực tế": round((w * h) / 1000000, 3),
                                    "M2 tính tiền": round(area, 2),
                                    "Thành tiền ($$)": round(area * unit_price, 2)
                                })
                
                if data_rows:
                    df = pd.DataFrame(data_rows)
                    st.subheader(f"📍 Công trình: {address_found}")
                    st.table(df)
                    
                    # Tạo file Excel trong bộ nhớ tạm
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    
                    # Đặt tên file (xoá ký tự lạ)
                    clean_name = re.sub(r'[\\/*?:"<>|]', "", address_found).strip().replace(" ", "_")
                    xls_filename = f"{clean_name}.xlsx"
                    
                    # GỬI THẲNG LÊN CLOUD
                    if upload_to_drive(output.getvalue(), xls_filename, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", folder_measure):
                        st.success(f"✅ ĐÃ LƯU: '{xls_filename}' VÀO FOLDER SỔ ĐO TRÊN DRIVE!")
                    
                    st.download_button("Tải file về máy", output.getvalue(), xls_filename)

    # B. PHẦN XỬ LÝ INVOICE
    else:
        invoice_file = st.camera_input("CHỤP INVOICE CẦN LƯU")
        if invoice_file:
            with st.spinner('Đang tạo PDF và gửi lên Cloud...'):
                pdf_bytes = export_as_pdf(invoice_file)
                pdf_filename = "Invoice_Moi.pdf"
                
                if upload_to_drive(pdf_bytes, pdf_filename, "application/pdf", folder_invoice):
                    st.success("✅ ĐÃ LƯU: INVOICE VÀO FOLDER INVOICE TRÊN DRIVE!")
                
                st.download_button("Tải PDF về máy", pdf_bytes, pdf_filename)
else:
    st.error("Chưa có API Key kìa Jimmy ơi!")
