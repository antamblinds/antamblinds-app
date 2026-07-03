import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH HUB
st.set_page_config(page_title="An Tam Blinds Tool", layout="wide")
st.header("🏠 AN TAM BLINDS - CÔNG CỤ SỔ ĐO & INVOICE")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

# Khởi tạo bộ nhớ tạm
if 'results' not in st.session_state:
    st.session_state.results = None
if 'address' not in st.session_state:
    st.session_state.address = "Khach_Hang"

if api_key:
    genai.configure(api_key=api_key)
    # Tự động chọn model AI còn sống
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(models[0])

    # MENU ĐƠN GIẢN BÊN TRÁI
    st.sidebar.title("CÔNG VIỆC")
    task = st.sidebar.radio("CHỌN LOẠI:", ["📝 Ghi Sổ Đo -> Excel", "🧾 Lưu Invoice -> PDF"])

    # --- PHẦN 1: GHI SỔ ĐO ---
    if task == "📝 Ghi Sổ Đo -> Excel":
        st.subheader("📝 CHỤP SỔ ĐO (Tự động chuyển Excel)")
        img_file = st.camera_input("CHỤP TỜ GIẤY ĐO")
        
        if img_file:
            if st.button("🚀 XÁC NHẬN ĐỌC SỐ ĐO"):
                with st.spinner('AI đang làm việc...'):
                    try:
                        img = PIL.Image.open(img_file)
                        prompt = "Read address and measurements. Format: ADDRESS: [addr] DATA: [Location | Width | Height]"
                        res = model.generate_content([prompt, img])
                        st.session_state.results = res.text
                        st.success("Đã đọc xong!")
                    except Exception as e:
                        st.error(f"Máy bận hoặc lỗi: {e}")

        if st.session_state.results:
            raw = st.session_state.results
            st.info(raw)
            
            rows = []
            # Tìm địa chỉ làm tên file
            addr_search = re.search(r'ADDRESS:\s*(.*)', raw)
            if addr_search:
                st.session_state.address = addr_search.group(1).split('\n')[0].strip().replace(" ","_").replace(",","")

            # Tìm số đo Ngang x Cao
            matches = re.findall(r'([^|\n]+?)\s*[|:]?\s*(\d{3,4})\s*[xX*|]\s*(\d{3,4})', raw)
            for m in matches:
                rows.append({"Vị trí": m[0].strip(), "Ngang (mm)": m[1], "Cao (mm)": m[2]})
            
            if rows:
                df = pd.DataFrame(rows)
                st.table(df) # Hiện bảng cho Jimmy kiểm tra
                
                out_ex = BytesIO()
                df.to_excel(out_ex, index=False)
                st.download_button(
                    label=f"📥 TẢI EXCEL: {st.session_state.address}.xlsx", 
                    data=out_ex.getvalue(), 
                    file_name=f"{st.session_state.address}.xlsx"
                )

    # --- PHẦN 2: LƯU INVOICE ---
    else:
        st.subheader("🧾 CHUYỂN INVOICE/RECEIPT SANG PDF")
        pdf_name = st.text_input("Nhập tên khách/Địa chỉ để đặt tên file:", "Invoice_AnTam")
        inv_img = st.camera_input("CHỤP HÓA ĐƠN")
        
        if inv_img:
            with st.spinner('Đang tạo file PDF...'):
                try:
                    pdf = FPDF()
                    pdf.add_page()
                    img_p = PIL.Image.open(inv_img)
                    img_p.save("temp.jpg")
                    pdf.image("temp.jpg", x=10, y=10, w=190)
                    st.download_button(
                        label="📥 TẢI FILE PDF VỀ MÁY", 
                        data=pdf.output(dest='S').encode('latin-1'), 
                        file_name=f"{pdf_name}.pdf"
                    )
                except Exception as e:
                    st.error(f"Lỗi tạo PDF: {e}")
else:
    st.error("Ông chưa dán mã API vào phần Secrets của Streamlit kì
