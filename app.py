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
st.header("🏠 An Tam Blinds - Báo Giá Tự Động")

with st.sidebar:
    st.header("Cài đặt đơn giá")
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
            uploaded_file = st.camera_input("Chụp sổ đo thực tế")
            if uploaded_file:
                with st.spinner('Đang soi chi tiết số đo từ ảnh...'):
                    img = PIL.Image.open(uploaded_file)
                    # Lệnh AI: Nhấn mạnh việc đọc con số CHÍNH XÁC từ ảnh
                    prompt = """
                    Bạn là trợ lý đọc số liệu cực kỳ chính xác cho An Tam Blinds. 
                    NHIỆM VỤ:
                    1. Tìm ĐỊA CHỈ khách hàng trên tờ giấy.
                    2. Đọc CHÍNH XÁC từng con số Rộng và Cao của mỗi cửa (không được làm tròn số đo thực tế).
                    3. Trình bày kích thước theo dạng: [SốRộng]/[SốCao].lkc 
                    
                    TRẢ VỀ ĐÚNG CẤU TRÚC SAU:
                    ADDRESS: [Địa chỉ]
                    DATA:
                    [Vị trí] | [SốRộng]/[SốCao].lkc | [Ghi chú]
                    
                    Ví dụ: Nếu ảnh ghi Rộng 1523 và Cao 1457 thì phải ghi là 1523/1457.lkc
                    Tuyệt đối không bịa số. Trả về tiếng Việt.
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
                                size_str = parts[1].strip() # Ví dụ: 1523/1457.lkc (số từ ảnh)
                                notes = parts[2].strip() if len(parts) > 2 else ""
                                
                                # Tách số đo chính xác để tính diện tích
                                match = re.search(r"(\d+)/(\d+)", size_str)
                                if match:
                                    w_mm = float(match.group(1))
                                    h_mm = float(match.group(2))
                                    # Diện tích m2 thực tế
                                    area_real = (w_mm * h_mm) / 1_000_000
                                    # Áp dụng luật tính tiền của Jimmy (tối thiểu 1.5m2)
                                    area_billing = max(area_real, 1.5)
                                    total = area_billing * unit_price
                                    
                                    data_rows.append({
                                        "Vị trí": vi_tri,
                                        "Kích thước (.lkc)": size_str, # Đây là số đo CHUẨN từ ảnh
                                        "M2 thực tế": round(area_real, 2),
                                        "M2 tính tiền": round(area_billing, 2),
                                        "Thành tiền ($$)": round(total, 2),
                                        "Ghi chú": notes
                                    })
                    
                    if data_rows:
                        df = pd.DataFrame(data_rows)
                        st.subheader(f"📊 Báo giá cho: {address_val}")
                        st.table(df)
                        
                        file_name_final = f"{clean_filename(address_val)}.xlsx"
                        
                        output_ex = BytesIO()
                        with pd.ExcelWriter(output_ex, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        
                        st.download_button(
                            label=f"📥 TẢI EXCEL: {file_name_final}",
                            data=output_ex.getvalue(),
                            file_name=file_name_final,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.warning("AI không đọc được số liệu. Jimmy hãy chụp ảnh vuông góc và rõ nét hơn nhé!")
    except Exception as e:
        st.error(f"Lỗi: {e}")
else:
    st.info("Nhớ dán API Key vào Secrets nha Jimmy!")
