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

# SỬA LỖI TẠI ĐÂY: Hàm chuyển ảnh thành PDF đảm bảo định dạng chuẩn
def export_as_pdf(image_file):
    pdf = FPDF()
    pdf.add_page()
    img = PIL.Image.open(image_file)
    # Tự động canh ảnh vừa trang giấy A4
    pdf.image(img, x=10, y=10, w=190)
    # Ép kiểu về bytes để Streamlit không báo lỗi bytearray
    return bytes(pdf.output())

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # Tự động dò tìm bộ não AI khả dụng
        raw_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in raw_models if "flash" in m), raw_models[0] if raw_models else None)
        
        if model_name:
            model = genai.GenerativeModel(model_name)
            st.sidebar.success(f"✅ Đã kết nối: {model_name}")

            task = st.radio("Chọn loại công việc:", ["Ghi Sổ Đo (.l.kc) -> Xuất EXCEL", "Chụp Invoice -> Xuất PDF"])

            if task == "Ghi Sổ Đo (.l.kc) -> Xuất EXCEL":
                uploaded_file = st.camera_input("Chụp ảnh tờ sổ đo")
                if uploaded_file:
                    with st.spinner('Đang tạo file Excel sạch...'):
                        img = PIL.Image.open(uploaded_file)
                        prompt = """
                        Bạn là thư ký của An Tam Blinds. Hãy đọc ảnh sổ đo và liệt kê:
                        1. Địa chỉ công trình.
                        2. Kích thước DẠNG: Rộng/Cao.l.kc (Ví dụ: 1525/1458.l.kc)
                        3. Hướng L/R và Tên Vải.
                        Lưu ý: TUYỆT ĐỐI KHÔNG ghi 'Mục 1', 'Hạng mục'. Chỉ liệt kê danh sách sạch. Trả về tiếng Việt.
                        """
                        response = model.generate_content([prompt, img])
                        st.code(response.text)
                        
                        df = pd.DataFrame([{"Data": response.text}])
                        output_ex = BytesIO()
                        with pd.ExcelWriter(output_ex, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        st.download_button("📥 Tải về Excel", output_ex.getvalue(), "SoDo_AnTam.xlsx")

            else:
                # CHỖ NÀY ĐÃ SỬA LỖI: Invoice xuất PDF
                invoice_file = st.camera_input("Chụp ảnh hóa đơn mua hàng")
                if invoice_file:
                    with st.spinner('Đang chuyển hóa đơn thành PDF...'):
                        try:
                            pdf_bytes = export_as_pdf(invoice_file)
                            st.success("✅ Đã chuyển đổi thành PDF thành công!")
                            st.download_button(
                                label="📥 Tải về Invoice (PDF)",
                                data=pdf_bytes,
                                file_name="Invoice_AnTam.pdf",
                                mime="application/pdf"
                            )
                        except Exception as pdf_err:
                            st.error(f"Lỗi tạo PDF: {pdf_err}")
        else:
            st.error("Không tìm thấy bộ não AI khả dụng.")

    except Exception as e:
        st.error(f"Lỗi: {e}. Jimmy nhấn F5 lại nhé!")
else:
    st.warning("Jimmy ơi, dán API Key vào Secrets nha!")
