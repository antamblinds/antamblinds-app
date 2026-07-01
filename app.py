import streamlit as st
import google.generativeai as genai
import PIL.Image

st.set_page_config(page_title="An Tam Blinds Admin", layout="centered")
st.header("🛠 An Tam Blinds v1.0 (Stable)")

# Sidebar để dán Key
api_key = st.sidebar.text_input("Dán Google API Key vào đây:", type="password")

if not api_key:
    st.info("Jimmy ơi, ông hãy dán cái mã API Key vào ô bên trái nhé!")
else:
    try:
        genai.configure(api_key=api_key)
        
        # CHIÊU CUỐI: Tự tìm danh sách các bộ não đang mở trong tài khoản của ông
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ưu tiên tìm bản Flash hoặc Pro, nếu không thấy thì lấy đại cái đầu tiên trong danh sách
        model_name = ""
        for m in models:
            if "gemini-1.5-flash" in m:
                model_name = m
                break
        if not model_name:
            model_name = models[0] if models else None

        if model_name:
            model = genai.GenerativeModel(model_name)
            st.sidebar.success(f"Đã kết nối: {model_name}")
            
            uploaded_file = st.camera_input("Chụp ảnh sổ đo ngay")

            if uploaded_file:
                with st.spinner('AI đang đọc sổ đo...'):
                    image = PIL.Image.open(uploaded_file)
                    
                    # Lệnh ép AI ra định dạng .l.kc cho Jimmy
                    prompt = """
                    Bạn là trợ lý cho An Tam Blinds. Hãy đọc ảnh sổ đo rèm và liệt kê:
                    1. Địa chỉ công trình.
                    2. Kích thước TRÌNH BÀY ĐÚNG DẠNG: Rộng/Cao.l.kc (Ví dụ: 1234/1546.l.kc)
                    3. Hướng L/R và Tên Vải.
                    Trả về kết quả tiếng Việt rõ ràng, để trong khung Code cho dễ copy.
                    """
                    
                    response = model.generate_content([prompt, image])
                    st.subheader("📋 KẾT QUẢ ĐƠN HÀNG (.l.kc):")
                    st.code(response.text, language="text")
                    st.success("Xong rồi ông nội ơi!")
        else:
            st.error("Tài khoản của ông chưa kích hoạt bộ não nào cả. Hãy kiểm tra lại bên AI Studio!")

    except Exception as e:
        st.error(f"Lỗi rồi: {e}. Thử nhấn F5 nhé!")
