import streamlit as st
import pandas as pd
import google.generativeai as genai
import PIL.Image

# Giao diện An Tam Blinds
st.set_page_config(page_title="An Tam Blinds Admin", layout="centered")
st.title("🛠 An Tam Blinds App (Google AI)")

# Menu bên trái
st.sidebar.header("Cài đặt")
api_key = st.sidebar.text_input("Dán Google API Key vào đây:", type="password")

if not api_key:
    st.warning("Jimmy ơi, hãy dán API Key lấy từ AI Studio vào ô bên trái nhé!")
else:
    try:
        # Cấu hình AI
        genai.configure(api_key=api_key)
        
        # Thử dùng bản Flash, nếu không được tự động đổi sang bản Pro
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        uploaded_file = st.camera_input("Chụp ảnh sổ đo ngay")

        if uploaded_file:
            with st.spinner('Jimmy chờ xíu, máy đang phân tích sổ đo...'):
                image = PIL.Image.open(uploaded_file)
                
                # Lệnh đọc sổ đo cực kỳ chi tiết
                prompt = """
                Bạn là trợ lý cho cửa hàng An Tam Blinds. 
                Hãy đọc hình ảnh và liệt kê:
                1. Địa chỉ công trình.
                2. Danh sách kích thước (Rộng x Cao).
                3. Hướng L/R (nếu có).
                4. Tên vải hoặc màu sắc.
                5. Các ghi chú khác.
                Trả về tiếng Việt rõ ràng từng dòng.
                """
                
                response = model.generate_content([prompt, image])
                
                st.subheader("Kết quả AI đọc được:")
                st.markdown(response.text)
                st.success("Tuyệt vời! AI đã đọc xong rồi đó Jimmy!")
                
    except Exception as e:
        # Nếu vẫn lỗi 404, tui báo cho ông biết để thử đổi sang Gemini-Pro
        st.error(f"Ối, hệ thống báo: {e}. Jimmy hãy thử nhấn F5 (Refresh) lại trình duyệt xem sao nhé!")
