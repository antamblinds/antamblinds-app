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
    st.header("Cài đặt đơn giá")
    unit_price = st.number_input("Nhập đơn giá ($$/m2):", min_value=0.0, value=100.0, step=5.0)
    st.info("Luật: Dưới 1.5m2 tính 1.5m2")

def export_as_pdf(image_file):
    pdf = FPDF()
    pdf.add_page()
    img = PIL.Image.open(image_file)
    pdf.image(img, x=10, y=10, w=190)
    return bytes(pdf.output())

# Hàm làm sạch địa chỉ để đặt tên file
def clean_filename(text):
    # Xóa các ký tự không được phép trong tên file
    clean_name = re.sub(r'[\\/*?:"<>|]', "", text)
    return clean_name.strip().replace(" ", "_")

if api_key:
    try:
        genai.configure(api_key=api_key)
        raw_m = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in raw_m if "flash" in m), raw_models[0])
        model = genai.GenerativeModel(model_name)

        task = st.radio("Chọn loại công việc:", ["Ghi Sổ Đo & Tính Tiền -> EXCEL", "Chụp Invoice -> Xuất PDF"])

        if task == "Ghi Sổ Đo & Tính Tiền -> EXCEL":
            uploaded_file = st.camera_input("Chụp sổ đo rèm")
            if uploaded_file:
                with st.spinner('Đang đọc địa chỉ và tính toán...'):
                    img = PIL.Image.open(uploaded_file)
                    # Lệnh AI: Yêu cầu lấy địa chỉ ra dòng đầu tiên
                    prompt = """
                    Bạn là trợ lý cho An Tam Blinds. Hãy đọc ảnh sổ đo và:
                    1. Tìm địa chỉ công trình chính.
                    2. Liệt kê danh sách cửa theo định dạng: [Vị trí] | [Kích thước Rộng/Cao.l.kc] | [Ghi chú]
                    Trả về theo cấu trúc:
                    Địa chỉ: [Tên địa chỉ tìm thấy]
                    [Dữ liệu các dòng cửa...]
                    """
                    response = model.generate_content([prompt, img])
                    text_data = response.text
                    st.code(text_data)
                    
                    # --- BÓC TÁCH ĐỊA CHỈ & DỮ LIỆU ---
                    lines = text_data.strip().split('\n')
                    address_found = "DonHang_AnTam" # Tên mặc định nếu không tìm thấy
                    data_rows = []
                    
                    for line in lines:
                        if line.startswith("Địa chỉ:"):
                            address_found = line.replace("Địa chỉ:", "").strip()
                        elif "|" in line:
                            parts = line.split("|")
                            vi_tri = parts[0].strip()
                            size_str = parts[1].strip()
                            ghi_chu = parts[2].strip() if len(parts) > 2 else ""
                            
                            match = re.search(r"(\d+)/(\d+)", size_str)
                            if match:
                                w_mm = float(match.group(1))
                                h_mm = float(match.group(2))
                                area_real = (w_mm * h_mm) / 1_000_000
                                area_final = max(area_real, 1.5)
                                total = area_final * unit_price
                                
                                data_rows.append({
                                    "Vị trí": vi_tri, "Kích thước gốc": size_str,
                                    "Diện tích thực (m2)": round(area_real, 2),
                                    "Diện tích tính tiền (m2)": round(area_final, 2),
                                    "Thành tiền ($$)": round(total, 2), "Ghi chú": ghi_chu
                                })
                    
                    if data_rows:
                        df = pd.DataFrame(data_rows)
                        st.dataframe(df)
                        total_bill = df["Thành tiền ($$)"].sum()
                        st.metric(f"TỔNG CỘNG ({address_found})", f"$${total_bill:,.2f}")
                        
                        # ĐẶT TÊN FILE THEO ĐỊA CHỈ
                        final_filename = f"{clean_filename(address_found)}.xlsx"
                        
                        output_ex = BytesIO()
                        with pd.ExcelWriter(output_ex, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        
                        st.download_button(
                            label=f"📥 Tải File: {final_filename}",
                            data=output_ex.getvalue(),
                            file_name=final_filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.warning("Không đọc được số liệu, Jimmy chụp lại rõ hơn nhé!")

        else:
            invoice_file = st.camera_input("Chụp Invoice")
            if invoice_file:
                pdf_bytes = export_as_pdf(invoice_file)
                st.download_button("📥 Tải về Invoice (PDF)", pdf_bytes, "Invoice_AnTam.pdf", "application/pdf")

    except Exception as e:
        st.error(f"Lỗi: {e}")
else:
    st.warning("Dán API Key vào Secrets nha Jimmy!")
