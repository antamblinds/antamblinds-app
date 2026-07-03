import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="An Tam Tool", layout="wide")
st.header("🏠 AN TAM BLINDS - CÔNG CỤ SỔ ĐO & PDF")

# Lấy API Key
api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

# Khởi tạo bộ nhớ tạm
if 'results' not in st.session_state:
    st.session_state.results = None
if 'address' not in st.session_state:
    st.session_state.address = "Khach_Hang"

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Tự tìm model AI
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model = genai.GenerativeModel(available_models[0])

        # MENU BÊN TRÁI
        st.sidebar.title("CÔNG VIỆC")
        task = st.sidebar.radio("CHỌN LOẠI:", ["📝 Ghi Sổ Đo -> Excel", "🧾 Lưu Invoice -> PDF"])

        if task == "📝 Ghi Sổ Đo -> Excel":
            st.subheader("📝 CHỤP SỔ ĐO ĐỂ RA FILE EXCEL")
            img_file = st.camera_input("CHỤP TỜ GIẤY")
            
            if img_file:
                if st.button("🚀 BẮT ĐẦU ĐỌC SỐ ĐO"):
                    with st.spinner('AI đang làm việc...'):
                        try:
                            img = PIL.Image.open(img_file)
                            prompt = "Read address and measurements. Format: ADDRESS: [addr] DATA: [Location | Width | Height]"
                            res = model.generate_content([prompt, img])
                            st.session_state.results = res.text
                            st.success("Xong!")
                        except Exception as e:
                            st.error(f"Lỗi: {e}")

            if st.session_state.results:
                raw_text = st.session_state.results
                st.info(raw_text)
                
                rows = []
                # Lấy địa chỉ làm tên file
                addr_search = re.search(r'ADDRESS:\s*(.*)', raw_text, re.IGNORECASE)
                if addr_search:
                    st.session_state.address = addr_search.group(1).split('\n')[0].strip().replace(" ","_").replace(",","")

                # Lấy số đo Ngang x Cao
                matches = re.findall(r'([^|\n]+?)\s*[|:]?\s*(\d{3,4})\s*[xX*|]\s*(\d{3,4})', raw_text)
                for m in matches:
                    rows.append({"Vị trí": m[0].strip(), "Ngang (mm)": m[1], "Cao (mm)": m[2]})
                
                if rows:
                    df = pd.DataFrame(rows)
                    st.table(df)
                    
                    # Nút tải Excel
                    out_ex = BytesIO()
                    with pd.ExcelWriter(out_ex, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    st.download_button(
                        label=f"📥 TẢI EXCEL: {st.session_state.address}.xlsx",
                        data=out_ex.getvalue(),
                        file_name=f"{st.session_state.address}.xlsx"
                    )

        else: # HÓA ĐƠN PDF
            st.subheader("🧾 CHỤP HÓA ĐƠN ĐỂ RA FILE PDF")
            pdf_name = st.text_input("Tên khách hàng:", "Invoice_AnTam")
            inv_img = st.camera_input("CHỤP HÓA ĐƠN")
            
            if inv_img:
                with st.spinner('Đang tạo PDF...'):
                    try:
                        pdf = FPDF()
                        pdf.add_page()
                        img_pil = PIL.Image.open(inv_img)
                        img_pil.save("temp.jpg")
                        pdf.image("temp.jpg", x=10, y=10, w=190)
                        st.download_button(
                            label="📥 TẢI FILE PDF",
                            data=pdf.output(dest='S').encode('latin-1'),
                            file_name=f"{pdf_name}.pdf"
                        )
                    except Exception as e_pdf:
                        st.error(f"Lỗi PDF: {e_pdf}")

    except Exception as e_main:
        st.error(f"Lỗi hệ thống: {e_main}")
else:
    st.error("Lỗi: Jimmy dán mã API vào phần Secrets nhanh lên nào!")
