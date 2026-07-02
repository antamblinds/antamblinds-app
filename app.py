import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from fpdf import FPDF
from io import BytesIO
import re

# --- Cấu hình hệ thống ---
api_key = st.secrets.get("GEMINI_API_KEY")

st.set_page_config(page_title="An Tam Blinds - Báo Giá Pro", layout="wide")
st.header("🏠 An Tam Blinds - Báo Giá Tự Động")

with st.sidebar:
    st.header("Cài đặt báo giá")
    # Cho phép Jimmy nhập đơn giá vải/rèm mỗi lần sử dụng
    unit_price = st.number_input("Nhập đơn giá ($$/m2):", min_value=0.0, value=100.0, step=5.0)
    st.info("Luật: Dưới 1.5m2 tính 1.5m2")

def export_as_pdf(image_file):
    pdf = FPDF()
    pdf.add_page()
    img = PIL.Image.open(image_file)
    pdf.image(img, x=10, y=10, w=190)
    return bytes(pdf.output())

if api_key:
    try:
        genai.configure(api_key=api_key)
        raw_m = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in raw_m if "flash" in m), raw_m[0])
        model = genai.GenerativeModel(model_name)

        task = st.radio("Chọn loại công việc:", ["Ghi Sổ Đo & Tính Tiền -> EXCEL", "Chụp Invoice -> Xuất PDF"])

        if task == "Ghi Sổ Đo & Tính Tiền -> EXCEL":
            uploaded_file = st.camera_input("Chụp ảnh sổ đo rèm")
            if uploaded_file:
                with st.spinner('Đang tính toán báo giá...'):
                    img = PIL.Image.open(uploaded_file)
                    prompt = """
                    Bạn là trợ lý báo giá cho An Tam Blinds. Hãy đọc ảnh sổ đo và liệt kê danh sách cửa.
                    Định dạng mỗi dòng bắt buộc: [Vị trí] | [Kích thước Rộng/Cao.l.kc] | [Ghi chú]
                    Ví dụ: Phòng khách | 1500/1200.l.kc | Vải Sage Green
                    QUY TẮC: Chỉ trả về dữ liệu các dòng, không ghi chữ thừa.
                    """
                    response = model.generate_content([prompt, img])
                    text_data = response.text
                    
                    # --- XỬ LÝ DỮ LIỆU & TÍNH TOÁN ---
                    lines = text_data.strip().split('\n')
                    data_rows = []
                    for line in lines:
                        if "|" in line:
                            parts = line.split("|")
                            vi_tri = parts[0].strip()
                            size_str = parts[1].strip() # Dạng: 1525/1458.l.kc
                            ghi_chu = parts[2].strip() if len(parts) > 2 else ""
                            
                            # Tách Rộng và Cao bằng Regex
                            match = re.search(r"(\d+)/(\d+)", size_str)
                            if match:
                                w_mm = float(match.group(1))
                                h_mm = float(match.group(2))
                                # Tính diện tích thực (m2)
                                area_real = (w_mm * h_mm) / 1_000_000
                                # Áp dụng luật 1.5m2 của Jimmy
                                area_final = max(area_real, 1.5)
                                # Tính tiền
                                total = area_final * unit_price
                                
                                data_rows.append({
                                    "Vị trí": vi_tri,
                                    "Rộng (mm)": w_mm,
                                    "Cao (mm)": h_mm,
                                    "Kích thước gốc": size_str,
                                    "Diện tích thực (m2)": round(area_real, 2),
                                    "Diện tích tính tiền (m2)": round(area_final, 2),
                                    "Đơn giá": unit_price,
                                    "Thành tiền ($$)": round(total, 2),
                                    "Ghi chú": ghi_chu
                                })
                    
                    if data_rows:
                        df = pd.DataFrame(data_rows)
                        st.subheader("📊 Bảng Báo Giá Chi Tiết")
                        st.dataframe(df) # Hiện bảng đẹp mắt cho Jimmy
                        
                        # Tổng cộng cuối đơn
                        total_bill = df["Thành tiền ($$)"].sum()
                        st.metric("TỔNG CỘNG ĐƠN HÀNG", f"$${total_bill:,.2f}")
                        
                        output_ex = BytesIO()
                        with pd.ExcelWriter(output_ex, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        
                        st.download_button("📥 Tải File EXCEL Báo Giá", output_ex.getvalue(), "BaoGia_AnTam_Pro.xlsx")
                    else:
                        st.warning("Chụp ảnh lại rõ hơn chút đi ông, AI chưa tách được số!")

        else:
            invoice_file = st.camera_input("Chụp ảnh Invoice")
            if invoice_file:
                pdf_bytes = export_as_pdf(invoice_file)
                st.download_button("📥 Tải về Invoice (PDF)", pdf_bytes, "Invoice_AnTam.pdf", "application/pdf")

    except Exception as e:
        st.error(f"Lỗi: {e}")
else:
    st.warning("Jimmy ơi, dán API Key vào Secrets nha!")
