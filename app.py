import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="An Tam Blinds Pro", layout="centered")
st.header("🏠 An Tam Blinds - Admin Pro")

# --- Thanh menu bên trái ---
with st.sidebar:
    st.header("Cài đặt hệ thống")
    api_key = st.text_input("1. Dán Google API Key:", type="password")
    # Tui đã bỏ cái type="password" ở đây để hết lỗi
    drive_json = st.text_area("2. Dán JSON Drive (nếu có):", help="Dán nội dung file JSON để kết nối Drive")

if not api_key:
    st.info("Jimmy ơi, ông hãy dán API Key vào ô bên trái để bắt đầu nhé!")
else:
    try:
        genai.configure(api_key=api_key)
        
        # Tự động lấy bộ não AI
        raw_m = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in raw_m if "1.5-flash" in m), raw_m[0] if raw_m else None)
        
        if model_name:
            model = genai.GenerativeModel(model_name)
            
            task = st.radio("Ông muốn làm gì?", ["Ghi Sổ Đo (.l.kc)", "Chụp Hóa Đơn (Invoices)"])

            if task == "Ghi Sổ Đo (.l.kc)":
                uploaded_file = st.camera_input("Chụp ảnh tờ sổ đo")
                if uploaded_file:
                    with st.spinner('Đang bóc tách dữ liệu sạch...'):
                        image = PIL.Image.open(uploaded_file)
                        
                        # Lệnh ép AI bỏ chữ Hạng mục và ra đuôi .l.kc
                        prompt = """
                        Bạn là thư ký của An Tam Blinds. Hãy đọc sổ đo và liệt kê:
                        1. Địa chỉ công trình.
                        2. Danh sách kích thước dạng: Rộng/Cao.l.kc (Ví dụ: 1525/1458.l.kc)
                        3. Hướng L/R và Tên Vải.
                        
                        QUY TẮC: 
                        - KHÔNG ghi 'Mục 1', 'Hạng mục' hay số thứ tự.
                        - Chỉ liệt kê danh sách các dòng kích thước sạch sẽ.
                        - Trả về tiếng Việt.
                        """
                        response = model.generate_content([prompt, image])
                        st.subheader("📋 KẾT QUẢ ĐƠN HÀNG:")
                        st.code(response.text, language="text")
                        
                        # Nút tạo Excel nhanh
                        df = pd.DataFrame([{"Dữ liệu": response.text}])
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        st.download_button("📥 Tải file Excel", output.getvalue(), file_name="AnTam_DonHang.xlsx")
            else:
                st.camera_input("Chụp ảnh hóa đơn mua hàng (Invoices)")
                st.info("Khi ông chụp, ảnh sẽ hiện ở đây để ông lưu vào Drive.")

    except Exception as e:
        st.error(f"Lỗi rồi ông ơi: {e}")
