import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH
st.set_page_config(page_title="An Tam Tool", layout="wide")
st.header("🏠 AN TAM BLINDS - CÔNG CỤ TỐI ƯU")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

# BỘ NHỚ TẠM (Để không bao giờ bị tốn hạn mức AI vô ích)
if 'ocr_result' not in st.session_state:
    st.session_state.ocr_result = None

if api_key:
    genai.configure(api_key=api_key)
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(models[0])

    st.sidebar.title("MENU")
    task = st.sidebar.radio("CHỌN VIỆC:", ["📝 Ghi Số Đo -> Excel", "🧾 Lưu Invoice -> PDF"])

    if task == "📝 Ghi Sổ Đo -> Excel":
        img_file = st.camera_input("CHỤP SỔ ĐO")
        
        if img_file:
            # Chỉ hiện nút đọc khi có ảnh mới
            if st.button("🚀 BẮT ĐẦU ĐỌC SỐ ĐO (NHẤN 1 LẦN)"):
                with st.spinner('Đang đọc... Đợi tí nhé Jimmy!'):
                    try:
                        img = PIL.Image.open(img_file)
                        res = model.generate_content(["Read address and sizes. Format: ADDRESS: [addr] DATA: [Loc | W | H]", img])
                        st.session_state.ocr_result = res.text
                        st.success("Xong rồi ông ơi!")
                    except Exception as e:
                        if "429" in str(e):
                            st.warning("Google bắt nghỉ 1 phút. Ông đợi tí rồi bấm lại nha!")
                        else:
                            st.error(f"Lỗi: {e}")

        # Hiển thị kết quả đã lưu trong bộ nhớ (Không tốn thêm lượt AI)
        if st.session_state.ocr_result:
            raw = st.session_state.ocr_result
            st.info(raw)
            
            # Tách địa chỉ làm tên file
            addr = "Khach_An_Tam"
            addr_match = re.search(r'ADDRESS:\s*(.*)', raw, re.IGNORECASE)
            if addr_match:
                addr = addr_match.group(1).split('\n')[0].strip().replace(" ","_").replace(",","")

            rows = []
            matches = re.findall(r'([^|\n]+?)\s*[|:]?\s*(\d{3,4})\s*[xX*|]\s*(\d{3,4})', raw)
            for m in matches:
                rows.append({"Vị trí": m[0].strip(), "Ngang (mm)": m[1], "Cao (mm)": m[2]})
            
            if rows:
                df = pd.DataFrame(rows)
                st.table(df)
                out_ex = BytesIO()
                with pd.ExcelWriter(out_ex, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(f"📥 TẢI EXCEL: {addr}.xlsx", out_ex.getvalue(), f"{addr}.xlsx")

    else: # PHẦN PDF (Không dùng AI nên KHÔNG BAO GIỜ bị lỗi 429)
        pdf_name = st.text_input("Tên file:", "Invoice_AnTam")
        inv_img = st.camera_input("CHỤP HÓA ĐƠN")
        if inv_img:
            pdf = FPDF(); pdf.add_page()
            img_p = PIL.Image.open(inv_img); img_p.save("temp.jpg")
            pdf.image("temp.jpg", x=10, y=10, w=190)
            st.download_button("📥 TẢI PDF", pdf.output(dest='S').encode('latin-1'), f"{pdf_name}.pdf")
else:
    st.error("Dán mã API vào Secrets đi Jimmy!")
