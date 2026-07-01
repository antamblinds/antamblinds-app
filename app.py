import streamlit as st
import google.generativeai as genai
import PIL.Image

st.set_page_config(page_title="An Tam Blinds Admin", layout="centered")
st.title("🛠 An Tam Blinds App (Smart Version)")

st.sidebar.header("Cài đặt")
api_key = st.sidebar.text_input("Dán Google API Key vào đây:", type="password")

if not api_key:
    st.warning("Jimmy ơi, hãy dán API Key vào ô bên trái nhé!")
else:
    try:
        genai.configure(api_key=api_key)
        
        # Tự động tìm model khả dụng trong tài khoản của ông
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ưu tiên lấy bản Flash, nếu không có lấy bản Pro, nếu không có lấy bản đầu tiên tìm thấy
        model_name = 'models/gemini-1.5-flash' # Mặc định
        if 'models/gemini-1.5-flash' in available_models:
            model_name = 'models/gemini-1.5-flash'
        elif 'models/gemini-1.5-pro' in available_models:
            model_name = 'models/gemini-1.5-pro'
        elif available_models:
            model_name = available_models[0]

        model = genai.GenerativeModel(model_name)
        st.sidebar.success(f"Đang dùng: {model_name}")

        uploaded_file = st.camera_input("Chụp ảnh sổ đo ngay")

        if uploaded_file:
            with st.spinner('Jimmy chờ xíu, AI đang đọc sổ đo...'):
                image = PIL.Image.open(uploaded_file)
                prompt = "Đọc hình ảnh sổ đo này. Liệt kê Địa chỉ, Kích thước (Rộng/Cao.lkc), L/R, Vải. Trả về tiếng Việt."
                
                response = model.generate_content([prompt, image])
                st.subheader("Kết quả AI đọc được:")
                st.write(response.text)
                st.success("Xong rồi đó Jimmy ơi!")
                
    except Exception as e:
        st.error(f"Lỗi rồi ông ơi: {e}. Thử nhấn F5 lại nhé!")
