import streamlit as st
import pandas as pd
import google.generativeai as genai
import PIL.Image
import io

# Cấu hình giao diện App An Tam Blinds
st.set_page_config(page_title="An Tam Blinds Admin", layout="centered")
st.title("🛠 An Tam Blinds App (Google AI)")

# Sidebar để dán Key
st.sidebar.header("Cài đặt")
api_key = st.sidebar.text_input("Dán Google API Key vào đây:", type="password")

if not api_key:
    st.warning("Jimmy ơi, ông hãy dán cái API Key lấy từ AI Studio vào ô bên trái nhé!")
else:
    try:
        # Cấu hình Google AI
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        option = st.radio("Chọn loại:", ["Sổ đo công trình", "Hóa đơn Supplier"])
        uploaded_file = st.camera_input("Chụp ảnh sổ đo ngay")

        if uploaded_file:
            with st.spinner('Máy đang đọc dữ liệu, Jimmy chờ xíu...'):
                image = PIL.Image.open(uploaded_file)
                # Lệnh yêu cầu AI đọc sổ đo bằng tiếng Việt
                prompt = "Đây là sổ đo rèm cửa. Hãy đọc và liệt kê: 1. Địa chỉ, 2. Kích thước (Rộng/Cao.lkc), 3. Hướng L/R, 4. Vải, 5. Ghi chú. Trả về tiếng Việt rõ ràng từng dòng."
                
                response = model.generate_content([prompt, image])
                
                st.subheader("Kết quả AI đọc được:")
                # Hiển thị kết quả trong một ô văn bản để dễ copy
                result_text = st.text_area("Kết quả:", response.text, height=300)
                
                st.info("Sau khi AI đọc xong, Jimmy chỉ cần copy đoạn trên dán vào Excel là xong!")
                
    except Exception as e:
        st.error(f"Ối, có lỗi rồi: {e}. Ông kiểm tra lại cái API Key nhé!")
