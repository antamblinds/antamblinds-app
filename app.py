import streamlit as st
import pandas as pd
from openai import OpenAI
import json
import base64

# Cấu hình App An Tam Blinds
st.set_page_config(page_title="An Tam Blinds Admin", layout="centered")
st.title("🛠 An Tam Blinds App v1")

# Cài đặt thanh Sidebar bên trái
st.sidebar.header("Cài đặt")
api_key = st.sidebar.text_input("Dán OpenAI API Key vào đây:", type="password")

if not api_key:
    st.warning("Jimmy ơi, ông hãy dán cái API Key vào ô bên trái nhé!")
else:
    client = OpenAI(api_key=api_key)
    option = st.radio("Chọn loại:", ["Sổ đo công trình", "Hóa đơn Supplier"])
    
    # Nút chụp ảnh
    uploaded_file = st.camera_input("Chụp ảnh sổ đo ngay")

    if uploaded_file:
        with st.spinner('AI đang đọc dữ liệu, ông chờ xíu...'):
            img_bytes = uploaded_file.getvalue()
            base64_image = base64.b64encode(img_bytes).decode('utf-8')
            
            prompt = "Read image, return JSON. Fields: Address, Dimensions (Width/Height.lkc), L_R, Fabric, Notes. Vietnamese results."
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}],
                response_format={ "type": "json_object" }
            )
            
            res_data = json.loads(response.choices[0].message.content)
            st.subheader("Kết quả AI đọc được:")
            
            # Cho phép Jimmy chỉnh sửa lại dữ liệu
            final_data = {}
            for key, value in res_data.items():
                final_data[key] = st.text_input(f"{key}:", value)
                
            if st.button("Lưu & Xuất File Excel"):
                df = pd.DataFrame([final_data])
                csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("Tải File Excel về máy", data=csv, file_name="AnTam_Data.csv", mime='text/csv')
                st.success("Đã xong! Ông mở file Excel lên coi thử nhé.")
