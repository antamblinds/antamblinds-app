import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH HUB
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - CÔNG CỤ XUẤT FILE")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

# Bộ nhớ tạm
if 'final_data' not in st.session_state: st.session_state.final_data = None
if 'file_name_cust' not in st.session_state: st.session_state.file_name_cust = "Khach_Hang"

if api_key:
    genai.configure(api_key=api_key)
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(models[0])

    st.sidebar.title("DANH MỤC")
    task = st.sidebar.radio("CHỌN VIỆC:", ["📝 Ghi Số Đo -> Excel", "🧾 Lưu Invoice -> PDF"])

    if task == "📝 Ghi Sổ Đo -> Excel":
        img_file = st.camera_input("CHỤP SỔ ĐO")
        
        if img_file:
            if st.button("🚀 XÁC NHẬN ĐỌC SỐ ĐO"):
                with st.spinner('AI đang bóc tách số liệu...'):
                    try:
                        img = PIL.Image.open(img_file)
                        # Ép AI ghi đúng chữ ADDRESS để mình bắt tên file
                        prompt = "Identify the job address and measurements. MUST start with 'ADDRESS: [address]'. Then list data: [Location] | [Width] | [Height] | [Note]"
                        res = model.generate_content([prompt, img])
                        st.session_state.final_data = res.text
                        
                        # TÌM ĐỊA CHỈ ĐỂ ĐẶT TÊN FILE (Bắt cả tiếng Anh lẫn tiếng Việt)
                        raw = res.text
                        addr_search = re.search(r'(ADDRESS:|Địa chỉ|Dia chi):\s*(.*)', raw, re.IGNORECASE)
                        if addr_search:
                            # Lấy địa chỉ, bỏ dấu phẩy và khoảng trắng để làm tên file sạch
                            clean_addr = addr_search.group(2).split('\n')[0].strip().replace(" ","_").replace(",","")
                            st.session_state.file_name_cust = clean_addr
                        st.success(f"Đã nhận diện địa chỉ: {st.session_state.file_name_cust}")
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

        if st.session_state.final_data:
            st.info(st.session_state.final_data)
            rows = []
            # Tách số đo
            matches = re.findall(r'([^|\n]+?)\s*[|:/xX]\s*(\d{3,4})\s*[|/xX]\s*(\d{3,4})', st.session_state.final_data)
            for m in matches:
                rows.append({
                    "Vị trí": m[0].strip(),
                    "Kích thước": f"{m[1]}/{m[2]}.L.kc",
                    "Địa chỉ khách": st.session_state.file_name_cust.replace("_"," ")
                })
            
            if rows:
                df = pd.DataFrame(rows)
                st.table(df)
                
                # NÚT TẢI EXCEL - Tên file chính là địa chỉ
                out_ex = BytesIO()
                df.to_excel(out_ex, index=False)
                st.download_button(
                    label=f"📥 TẢI EXCEL: {st.session_state.file_name_cust}.xlsx",
                    data=out_ex.getvalue(),
                    file_name=f"{st.session_state.file_name_cust}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    else: # INVOICE
        inv_name = st.text_input("Gõ địa chỉ khách cho file PDF:", "Invoice_AnTam")
        inv_img = st.camera_input("CHỤP HÓA ĐƠN")
        if inv_img:
            pdf = FPDF(); pdf.add_page()
            img_p = PIL.Image.open(inv_img); img_p.save("temp.jpg")
            pdf.image("temp.jpg", x=10, y=10, w=190)
            st.download_button(f"📥 TẢI PDF {inv_name}", pdf.output(dest='S').encode('latin-1'), f"{inv_name}.pdf")
else:
    st.error("Dán API Key vào Secrets nha Jimmy!")
