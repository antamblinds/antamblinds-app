import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
import json
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. CỐ ĐỊNH CẤU HÌNH
st.set_page_config(page_title="An Tam Blinds Cloud", layout="wide")
st.header("🏠 AN TAM BLINDS - AUTO SYSTEM")

# Lấy bí mật (Xóa khoảng trắng cho chắc)
api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
drive_json = st.secrets.get("GOOGLE_DRIVE_JSON")
folder_id = st.secrets.get("FOLDER_MEASUREMENTS")

# Hàm gửi Drive
def upload_to_drive(content, name, folder):
    try:
        info = json.loads(drive_json)
        creds = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=creds)
        meta = {'name': name, 'parents': [folder]}
        media = MediaIoBaseUpload(BytesIO(content), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        service.files().create(body=meta, media_body=media).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi Drive: {e}")
        return False

# 2. CHẠY AI
if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # TỰ ĐỘNG DÒ MODEL NÀO CHẠY ĐƯỢC VỚI MÃ AQ
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ưu tiên lấy Flash, nếu không có thì lấy cái đầu tiên trong danh sách
        model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
        
        st.sidebar.success(f"Đã kết nối mã AQ! Đang dùng: {model_name}")
        model = genai.GenerativeModel(model_name)

        uploaded_file = st.camera_input("CHỤP SỔ ĐO")
        if uploaded_file:
            with st.spinner('Đang đọc số đo bằng mã AQ...'):
                img = PIL.Image.open(uploaded_file)
                # Ra lệnh AI ngắn gọn
                response = model.generate_content(["Read this. Format: ADDRESS: [addr] DATA: [Location|Width/Height]", img])
                
                st.write("### Kết quả đọc được:")
                st.info(response.text)
                
                # Tạo file Excel gửi Drive
                output = BytesIO()
                df = pd.DataFrame([{"Du Lieu": response.text}])
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                if upload_to_drive(output.getvalue(), "Don_Hang_Moi.xlsx", folder_id):
                    st.success("✅ QUÁ TUYỆT VỜI! FILE ĐÃ VÀO DRIVE RỒI JIMMY!")

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
else:
    st.error("Dán mã AQ vào Secrets đi ông ơi!")
