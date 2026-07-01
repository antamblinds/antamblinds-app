import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="An Tam Blinds Admin", layout="centered")
st.header("🏠 An Tam Blinds - Quản lý Đơn hàng & Invoice")

# Menu bên trái
api_key = st.sidebar.text_input("Dán Google API Key vào đây:", type="password")

if not api_key:
    st.info("Jimmy ơi, hãy dán API Key vào để bắt đầu nhé!")
else:
    try:
        genai.configure(api_key=api_key)
        # Tự động tìm model ổn định
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in available_models if "1.5-flash" in m), models[0])
        model = genai.GenerativeModel(model_name)

        # Chọn chế độ công việc
        task = st.radio("Ông muốn làm gì?", ["Đọc Sổ Đo Công Trình", "Chụp Hóa Đơn (Invoice)"])

        if task == "Đọc Sổ Đo Công Trình":
            uploaded_file = st.camera_input("Chụp ảnh sổ đo ngay")
            if uploaded_file:
                with st.spinner('AI đang bóc tách số liệu...'):
                    image = PIL.Image.open(uploaded_file)
                    # Lệnh "ép" AI bỏ chữ Hạng mục và xuất định dạng .l.kc
                    prompt = """
                    Bạn là thư ký của An Tam Blinds. Hãy đọc ảnh sổ đo và liệt kê theo cấu trúc sau:
                    - Địa chỉ công trình:
                    - Danh sách số đo: (Định dạng Rộng/Cao.l.kc, ví dụ: 1235/1546.l.kc)
                    - Vải và Hướng (nếu có).
                    Lưu ý: TUYỆT ĐỐI không ghi chữ 'Hạng mục 1', 'Hạng mục 2'. Chỉ liệt kê danh sách sạch.
                    """
                    response = model.generate_content([prompt, image])
                    st.subheader("📋 DỮ LIỆU ĐƠN HÀNG:")
                    st.code(response.text, language="text")
                    
                    # Nút tạo file Excel nhanh
                    if st.button("Tạo File Excel để gửi đi"):
                        df = pd.DataFrame([{"Dữ liệu": response.text}])
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        st.download_button("Nhấn vào đây để tải Excel về máy", output.getvalue(), file_name="DonHang_AnTam.xlsx")
                        st.success("Ông tải về máy rồi kéo vô Drive là xong bài!")

        else:
            # Chế độ chụp Invoices
            invoice_file = st.camera_input("Chụp ảnh Hóa đơn (Invoice)")
            if invoice_file:
                st.image(invoice_file, caption="Hóa đơn đã chụp")
                st.success("Hóa đơn đã được ghi nhận! Ông nhấn vào ảnh để lưu hoặc chia sẻ vô Drive nhé.")
                st.info("Để tự động đẩy vô Drive, tui sẽ chỉ ông cách cài đặt 'Service Account' ở bước kế tiếp nhé Jimmy!")

    except Exception as e:
        st.error(f"Lỗi: {e}. Nhấn F5 thử lại nhé!")
