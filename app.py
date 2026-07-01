import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="An Tam Blinds Pro", layout="centered")
st.header("🏠 An Tam Blinds - Admin Pro")

# --- Thanh menu cấu hình ---
with st.sidebar:
    st.header("Cài đặt hệ thống")
    api_key = st.text_input("1. Dán Google API Key:", type="password")
    drive_json = st.text_area("2. Dán JSON Drive (nếu có):", type="password", help="Để tự động gửi file vào Google Drive")

if not api_key:
    st.info("Jimmy ơi, hãy dán API Key vào ô bên trái để bắt đầu nhé!")
else:
    try:
        genai.configure(api_key=api_key)
        
        # Tự động lấy bộ não AI khả dụng
        raw_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Sửa lỗi 'models' is not defined bằng cách check list trực tiếp
        model_name = next((m for m in raw_models if "1.5-flash" in m), raw_models[0] if raw_models else None)
        
        if model_name:
            model = genai.GenerativeModel(model_name)
            
            task = st.radio("Ông muốn làm gì hôm nay?", ["Ghi Sổ Đo (.l.kc)", "Chụp Hóa Đơn (Invoices)"])

            if task == "Ghi Sổ Đo (.l.kc)":
                uploaded_file = st.camera_input("Chụp ảnh tờ sổ đo")
                if uploaded_file:
                    with st.spinner('Đang bóc tách dữ liệu...'):
                        image = PIL.Image.open(uploaded_file)
                        # Lệnh ép AI ra định dạng chuẩn của Jimmy
                        prompt = """
                        Bạn là thư ký của An Tam Blinds. Hãy đọc sổ đo và liệt kê:
                        1. Địa chỉ công trình.
                        2. Danh sách kích thước PHẢI trình bày dạng: Rộng/Cao.l.kc (Ví dụ: 1525/1458.l.kc)
                        3. Hướng L/R và Tên Vải.
                        
                        Lưu ý cực kỳ quan trọng: 
                        - KHÔNG ĐƯỢC ghi 'Hạng mục 1', 'Mục 1' hay bất kỳ tiêu đề thừa nào.
                        - Chỉ liệt kê danh sách sạch sẽ để copy vào Excel.
                        - Trả về tiếng Việt.
                        """
                        response = model.generate_content([prompt, image])
                        st.subheader("📋 DỮ LIỆU SẠCH:")
                        st.code(response.text, language="text")
                        
                        # Tạo file Excel để tải về nhanh
                        df = pd.DataFrame([{"DonHang": response.text}])
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        st.download_button("📥 Tải File Excel về máy", output.getvalue(), file_name="DonHang_AnTam.xlsx")

            else:
                # Phần chụp Invoice
                invoice_file = st.camera_input("Chụp ảnh hóa đơn mua hàng")
                if invoice_file:
                    st.image(invoice_file, caption="Hóa đơn đã ghi nhận")
                    st.success("Đã chụp xong Invoice! Jimmy có thể lưu ảnh này vào Google Drive nhé.")

        else:
            st.error("Không tìm thấy bộ não AI. Kiểm tra lại Key nhé!")

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
