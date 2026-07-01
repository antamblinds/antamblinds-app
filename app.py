import streamlit as st
import google.generativeai as genai
import PIL.Image

st.set_page_config(page_title="An Tam Blinds Admin", layout="centered")
st.title("🛠 An Tam Blinds App (Stable Version)")

st.sidebar.header("Cài đặt")
api_key = st.sidebar.text_input("Dán Google API Key vào đây:", type="password")

if not api_key:
    st.warning("Jimmy ơi, hãy dán API Key vào ô bên trái nhé!")
else:
    try:
        genai.configure(api_key=api_key)
        
        # Tự động tìm bộ não nào đang mở trong tài khoản của ông
        model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ưu tiên các dòng máy mạnh, nếu không có cái nào thì báo lỗi rõ ràng
        if 'models/gemini-1.5-flash' in model_list:
            model_name = 'models/gemini-1.5-flash'
        elif 'models/gemini-pro-vision' in model_list:
            model_name = 'models/gemini-pro-vision'
        elif 'models/gemini-1.5-pro' in model_list:
            model_name = 'models/gemini-1.5-pro'
        else:
            model_name = model_list[0] if model_list else None

        if model_name:
            model = genai.GenerativeModel(model_name)
            st.sidebar.success(f"Đang dùng: {model_name}")
            
            uploaded_file = st.camera_input("Chụp ảnh sổ đo công trình")

            if uploaded_file:
                with st.spinner('Đang đọc sổ đo cho Jimmy...'):
                    image = PIL.Image.open(uploaded_file)
                    # Lệnh vắt kiệt AI để ra định dạng .l.kc
                    prompt = """
                    Bạn là trợ lý An Tam Blinds. Hãy đọc ảnh và liệt kê:
                    1. Địa chỉ công trình.
                    2. Kích thước trình bày CỰC KỲ CHÍNH XÁC theo dạng: Width/Height.l.kc
                       (Ví dụ: 1235/1546.l.kc)
                    3. Hướng L/R và Vải bên cạnh.
                    Trả về tiếng Việt, để thông tin trong khung cho dễ copy.
                    """
                    response = model.generate_content([prompt, image])
                    st.subheader("📋 KẾT QUẢ ĐƠN HÀNG (.l.kc):")
                    st.code(response.text, language="text")
        else:
            st.error("Tài khoản này chưa mở bộ não AI nào. Jimmy kiểm tra lại Key nhé!")
                
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}. Jimmy nhấn F5 lại giúp tui!")
