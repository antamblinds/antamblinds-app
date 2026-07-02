import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from fpdf import FPDF
from io import BytesIO
import re

# --- Cấu hình hệ thống ---
api_key = st.secrets.get("GEMINI_API_KEY")

st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 An Tam Blinds - Quản lý Báo giá")

with st.sidebar:
    st.header("Cài đặt báo giá")
    unit_price = st.number_input("Nhập đơn giá ($$/m2):", min_value=0.0, value=100.0, step=5.0)

def export_as_pdf(image_file):
    pdf = FPDF()
    pdf.add_page()
    img = PIL.Image.open(image_file)
    pdf.image(img, x=10, y=10, w=190)
    return bytes(pdf.output())

def clean_filename(text):
    if not text: return "DonHang_AnTam"
    clean = re.sub(r'[\\/*?:"<>|]', "", text)
    return clean.strip().replace(" ", "_")

if api_key:
    try:
        genai.configure(api_key=api_key)
        raw_m = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in raw_m if "flash" in m), raw_m[0])
        model = genai.GenerativeModel(model_name)

        task = st.radio("Chọn loại công việc:", ["Ghi Sổ Đo (.lkc) & Tính Tiền", "Chụp Invoice -> PDF"])

        if task == "Ghi Sổ Đo (.lkc) & Tính Tiền":
            uploaded_file = st.camera_input("Chụp sổ đo")
            if uploaded_file:
                with st.spinner('Đang đọc địa chỉ và lấy số đo .lkc...'):
                    img = PIL.Image.open(uploaded_file)
                    prompt = """
                    Đọc ảnh sổ đo rèm và trả về đúng cấu trúc sau:
                    ADDRESS: [Địa chỉ khách hàng]
                    DATA:
                    Phòng/Vị trí | Rộng/Cao.lkc | Ghi chú
                    
                    LƯU Ý: Tuyệt đối giữ nguyên định dạng Rộng/Cao.lkc (ví dụ 1234/5678.lkc).
                    Không ghi Hạng mục 1, 2. Chỉ ghi dữ liệu sạch.
                    """
                    response = model.generate_content([prompt, img])
                    text_data = response.text
                    
                    address_val = "DonHang_AnTam"
                    data_rows = []
                    
                    lines = text_data.strip().split('\n')
                    for line in lines:
                        if line.startswith("ADDRESS:"):
                            address_val = line.replace("ADDRESS:", "").strip()
                        elif "|" in line:
                            parts = line.split("|")
                            if len(parts) >= 2:
                                vi_tri = parts[0].strip()
                                size_str = parts[1].strip() # Ví dụ: 1234/4562.lkc
                                notes = parts[2].strip() if len(parts) > 2 else ""
                                
                                # Tách số để tính diện tích
                                match = re.search(r"(\d+)/(\d+)", size_str)
                                if match:
                                    w_mm = float(match.group(1))
                                    h_mm = float(match.group(2))
                                    area = max((w_mm * h_mm) / 1_000_000, 1.5)
                                    total = area * unit_price
                                    
                                    data_rows.append({
                                        "Vị trí": vi_tri,
                                        "Kích thước (.lkc)": size_str, # Cột này giữ nguyên .lkc cho Jimmy
                                        "M2 tính tiền": round(area, 2),
                                        "Thành tiền ($$)": round(total, 2),
                                        "Ghi chú": notes
                                    })
                    
                    if data_rows:
                        df = pd.DataFrame(data_rows)
                        st.table(df)
                        
                        file_name_final = f"{clean_filename(address_val)}.xlsx"
                        
                        output_ex = BytesIO()
                        with pd.ExcelWriter(output_ex, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        
                        st.download_button(
                            label=f"📥 TẢI FILE: {file_name_final}",
                            data=output_ex.getvalue(),
                            file_name=file_name_final,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.warning("Không tìm thấy dữ liệu dòng. Jimmy chụp lại rõ hơn nhé!")
        else:
            invoice_file = st.camera_input("Chụp Invoice")
            if invoice_file:
                pdf_data = export_as_pdf(invoice_file)
                st.download_button("📥 Tải về PDF", pdf_data, "Invoice_AnTam.pdf", "application/pdf")

    except Exception as e:
        st.error(f"Lỗi: {e}")
else:
    st.info("Dán API Key vào Secrets nha Jimmy!")
