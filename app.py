import streamlit as st
import google.generativeai as genai
import PIL.Image

# Giao diện An Tam Blinds
st.set_page_config(page_title="An Tam Blinds Admin", layout="centered")
st.header("🛠 An Tam Blinds v1.0")

# Nhập Key ở thanh bên cạnh
api_key = st.sidebar.text_input("Dán Google API Key vào đây:", type="password")

if not api_key:
    st.info("Jimmy ơi, ông hãy dán cái API Key vào ô bên trái nhé!")
else:
    try:
        # Cấu hình AI
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Mở camera chụp ảnh
        uploaded_file = st.camera_input("Chụp ảnh sổ đo ngay")

        if uploaded_file:
            with st.spinner('Đang đọc sổ đo...'):
                image = PIL.Image.open(uploaded_file)
                
                # Lệnh ép AI ra định dạng .l.kc cho Jimmy
                prompt = """
                Bạn là trợ lý cho An Tam Blinds. Đọc ảnh và liệt kê:
                1. Địa chỉ.
                2. Kích thước TRÌNH BÀY ĐÚNG DẠNG: Rộng/Cao.l.kc (Ví dụ: 1234/5678.l.kc)
                3. Hướng L/R và Tên Vải.
                Trả về kết quả tiếng Việt dễ hiểu.
                """
                
                response = model.generate_content([prompt, image])
                st.subheader("📋 KẾT QUẢ (.l.kc):")
                st.code(response.text, language="text")
                st.success("Xong rồi ông ơi!")
                
    except Exception as e:
        st.error(f"Có lỗi nhỏ: {e}")
