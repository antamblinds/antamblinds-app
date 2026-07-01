import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from fpdf import FPDF
from io import BytesIO

# --- Cấu hình hệ thống ---
api_key = st.secrets.get("GEMINI_API_KEY")

st.set_page_config(page_title="An Tam Blinds Pro", layout="centered")
st.header("🏠 An Tam Blinds - Quản lý Đa năng")

# Hàm chuyển ảnh thành PDF cho Hóa đơn
def export_as_pdf(image_file):
    pdf = FPDF()
    pdf.add_page()
    img = PIL.Image.open(image_file)
    # Tự động canh ảnh vừa trang giấy A4
    pdf.image(img, x=10, y=10, w=190)
    return pdf.output()

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # --- CHIÊU CUỐI: TỰ ĐỘNG DÒ TÌM MODEL ---
        # Tìm xem tài khoản của ông có model nào chạy được thì lấy cái đó
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Ưu tiên Flash, nếu không có thì lấy cái đầu tiên tìm thấy
        model_name = next((m for m in available_models if "flash" in m), available_models[0] if available_models else None)
        
        if model_name:
            model = genai.GenerativeModel(model_name)
            st.sidebar.success(f"✅ Đã kết nối: {model_name}")

            task = st.radio("Chọn loại công việc:", ["Ghi Sổ Đo (.l.kc) -> Xuất EXCEL", "Chụp Invoice -> Xuất PDF"])

            if task == "Ghi Sổ Đo (.l.kc) -> Xuất EXCEL":
                uploaded_file = st.camera_input("Chụp ảnh tờ sổ đo")
                if uploaded_file:
                    with st.spinner('Đang tạo file Excel sạch...'):
                        img = PIL.Image.open(uploaded_file)
                        prompt = "Đọc ảnh sổ đo, liệt kê Địa chỉ và Kích thước dạng Rộng/Cao.l.kc. KHÔNG ghi chữ Hạng mục 1, 2. Trả về tiếng Việt."
                        response = model.generate_content([prompt, img])
                        st.code(response.text)
                        
                        # Tạo Excel
                        df = pd.DataFrame([{"Data": response.text}])
                        output_ex = BytesIO()
                        with pd.ExcelWriter(output_ex, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        st.download_button("📥 Tải về Excel", output_ex.getvalue(), "SoDo_AnTam.xlsx")

            else:
                invoice_file = st.camera_input("Chụp ảnh hóa đơn mua hàng")
                if invoice_file:
                    with st.spinner('Đang chuyển hóa đơn thành PDF...'):
                        pdf_data = export_as_pdf(invoice_file)
                        st.success("✅ Đã chuyển đổi thành PDF thành công!")
                        st.download_button("📥 Tải về Invoice (PDF)", pdf_data, "Invoice_AnTam.pdf")
        else:
            st.error("Không tìm thấy bộ não AI nào khả dụng. Kiểm tra lại Key nhé!")

    except Exception as e:
        st.error(f"Lỗi: {e}. Jimmy nhấn F5 lại nhé!")
else:
    st.warning("Jimmy ơi, dán API Key vào Secrets nha!")
