import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
import re
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# LẤY "CHÌA KHÓA"
api_key = st.secrets.get("GEMINI_API_KEY")
drive_json = st.secrets.get("GOOGLE_DRIVE_JSON")
folder_measure = st.secrets.get("FOLDER_MEASUREMENTS")

st.set_page_config(page_title="An Tam Blinds Cloud", layout="wide")
st.header("🏠 AN TAM BLINDS - TỰ ĐỘNG HÓA")

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

if api_key:
    # --- ĐOẠN NÀY QUAN TRỌNG: KHÔNG THÊM 'models/' NỮA ---
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash') 

    uploaded_file = st.camera_input("CHỤP SỔ ĐO")
    if uploaded_file:
        with st.spinner('Đang đọc số đo và gửi lên Drive...'):
            img = PIL.Image.open(uploaded_file)
            prompt = "Read image accurately. Find ADDRESS. List items: [Location] | [Width/Height.lkc]. Format: ADDRESS: [address] DATA: [items]"
            response = model.generate_content([prompt, img])
            text_data = response.text
            
            # Xử lý lấy số và tạo file Excel
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
                            w, h = float(match.group(1)), float(match.group(2))
                            area = max((w * h) / 1000000, 1.5)
                            data_rows.append({"Vị trí": parts[0].strip(), "Kích thước (.lkc)": parts[1].strip(), "M2": round(area, 2)})
            
            if data_rows:
                df = pd.DataFrame(data_rows)
                st.table(df)
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                filename = f"{address_found.replace(' ', '_')}.xlsx"
                if upload_to_drive(output.getvalue(), filename, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", folder_measure):
                    st.success(f"🚀 XONG! Đã vào Drive: {filename}")
else:
    st.error("Dán cái mã AQ đó vào Secrets đi Jimmy!")
