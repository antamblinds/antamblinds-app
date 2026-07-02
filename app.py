import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
import json
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. CẤU HÌNH HUB
st.set_page_config(page_title="An Tam Diagnosis", layout="wide")
st.header("🔍 KIỂM TRA KẾT NỐI DRIVE - AN TAM")

# Lấy bí mật
api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
drive_json = st.secrets.get("GOOGLE_DRIVE_JSON")
f_measure = st.secrets.get("FOLDER_MEASUREMENTS", "").strip().strip('.')

if drive_json:
    try:
        info = json.loads(drive_json)
        creds = service_account.Credentials.from_service_account_info(info)
        # Sử dụng API Drive v3
        service = build('drive', 'v3', credentials=creds)
        
        st.sidebar.info(f"🤖 Robot: {info.get('client_email')}")
        
        # KIỂM TRA: Robot thấy những folder nào?
        st.subheader("📁 Danh sách Folder robot nhìn thấy:")
        results = service.files().list(
            q="mimeType = 'application/vnd.google-apps.folder'",
            fields="files(id, name)"
        ).execute()
        folders = results.get('files', [])
        
        if not folders:
            st.warning("⚠️ Robot không thấy Folder nào hết! Chắc chắn ông phải bấm 'ENABLE' Drive API trong Cloud Console.")
        else:
            for f in folders:
                st.write(f"- Tên: **{f['name']}** | ID: `{f['id']}`")
                if f['id'] == f_measure:
                    st.success(f"🎯 ĐÃ KHỚP ID! Robot đã thấy folder '{f['name']}' của ông.")

        # CHẠY OCR VÀ GỬI THỬ
        img_input = st.camera_input("CHỤP THỬ PHÁT CUỐI")
        if img_input:
            with st.spinner('Đang thử gửi...'):
                out = BytesIO()
                pd.DataFrame([{"Test": "Success"}]).to_excel(out, index=False)
                
                # Thử gửi
                meta = {'name': 'Test_Ket_Noi.xlsx', 'parents': [f_measure]}
                media = MediaIoBaseUpload(out, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                service.files().create(body=meta, media_body=media).execute()
                st.success("✅ QUÁ ĐÃ JIMMY ƠI! NÓ VÀO DRIVE RỒI!")

    except Exception as e:
        if "404" in str(e):
            st.error(f"LỖI 404: Google bảo là Folder ID '{f_measure}' này không tồn tại hoặc ông chưa BẬT 'Google Drive API'.")
            st.markdown("👉 **[Bấm vào đây để BẬT Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)**")
        else:
            st.error(f"Lỗi khác: {e}")
