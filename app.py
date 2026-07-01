import streamlit as st
import google.generativeai as genai
import PIL.Image

st.set_page_config(page_title="An Tam Blinds Admin", layout="centered")
st.title("🛠 An Tam Blinds App (Định dạng .l.kc)")

st.sidebar.header("Cài đặt")
api_key = st.sidebar.text_input("Dán Google API Key vào đây:", type="password")

if not api_key:
    st.warning("Jimmy ơi, hãy dán API Key vào ô bên trái nhé!")
else:
    try:
        genai.configure(api_key=api_key)
        # Tự động chọn model
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = 'models/gemini-1.5-flash'
        if 'models/gemini-1.5-flash' in available_models: model_name = 'models/gemini-1.5-flash'
        
        model = genai.GenerativeModel(model_name)
        st.sidebar.success(f"App đã sẵn sàng!")

        uploaded_file = st.camera_input("Chụp ảnh sổ đo công trình")

        if uploaded_file:
            with st.spinner('Đang tạo định dạng .l.kc cho Jimmy...'):
                image = PIL.Image.open(uploaded_file)
                
                # Lệnh ép AI xuất đúng định dạng Rộng/Cao.l.kc
                prompt = """
                Bạn là thư ký chuyên nghiệp của An Tam Blinds. 
                Hãy đọc sổ đo và xuất dữ liệu theo đúng yêu cầu sau:
                1. Địa chỉ công trình.
                2. Kích thước PHẢI trình bày chính xác định dạng: Rộng/Cao.l.kc 
                   (Ví dụ: Nếu sổ ghi 1525 x 1458 thì bạn phải viết là 1525/1458.l.kc)
                3. Ghi chú thêm Hướng (L/R) và tên Vải bên cạnh.
                
                Kết quả trả về phải rõ ràng, ưu tiên để trong khung code để Jimmy dễ copy.
                """
                
                response = model.generate_content([prompt, image])
                
                st.subheader("📋 KẾT QUẢ ĐƠN HÀNG (.l.kc):")
                # Hiển thị kết quả trong khung Code để ông nhấn nút Copy cho lẹ
                st.code(response.text, language="text")
                
                st.success("Đúng định dạng ông cần rồi đó Jimmy!")
                
    except Exception as e:
        st.error(f"Lỗi: {e}. Thử nhấn F5 làm mới trang nhé!")
