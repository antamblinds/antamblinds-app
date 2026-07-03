import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - HỆ THỐNG QUẢN LÝ")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

# Khởi tạo bộ nhớ tạm
if 'results' not in st.session_state: st.session_state.results = None
if 'address' not in st.session_state: st.session_state.address = "Khach_Hang"

# HÀM TÍNH TIỀN "CHUẨN JIMMY"
def calculate_an_tam(w_mm, h_mm, item_type):
    try:
        w_m = float(w_mm) / 1000
        h_m = float(h_mm) / 1000
        if "Shutters" in item_type:
            area = max(w_m * h_m, 1.0)
            return round(area, 2), round(area * 140, 2), "m2"
        elif "Sheer" in item_type:
            return round(w_m, 2), round(w_m * 120, 2), "meters"
        elif "Blockout" in item_type:
            return round(w_m, 2), round(w_m * 145, 2), "meters"
        elif "Vertical" in item_type:
            area = max(w_m * h_m, 1.5)
            return round(area, 2), round(area * 65, 2), "m2"
        else: # Roller
            area = max(w_m * h_m, 1.5)
            return round(area, 2), round(area * 60, 2), "m2"
    except: return 0, 0, "error"

if api_key:
    genai.configure(api_key=api_key)
    # Tự chọn model AI
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(models[0])

    # --- MENU BÊN TRÁI ---
    st.sidebar.title("DANH MỤC")
    task = st.sidebar.radio("CHỌN VIỆC:", ["📝 Ghi Số Đo -> Excel", "🧾 Lưu Invoice -> PDF"])
    
    # --- PHẦN 1: GHI SỐ ĐO ---
    if task == "📝 Ghi Số Đo -> Excel":
        selected_item = st.sidebar.selectbox("Chọn loại rèm:", 
            ["Roller ($60/m2)", "Vertical ($65/m2)", "Shutters ($140/m2)", "Sheer Curtains ($120/m)", "Blockout Curtains ($$145/m)"])
        
        img_file = st.camera_input("CHỤP SỔ ĐO")
        if img_file:
            if st.button("🚀 BẤT ĐẦU ĐỌC VÀ TÍNH TIỀN"):
                with st.spinner('AI đang làm việc... (Nếu lỗi 429 hãy đợi 60s)'):
                    try:
                        img = PIL.Image.open(img_file)
                        res = model.generate_content(["Read address and sizes. Format: ADDRESS: [addr] DATA: [Loc | W | H]", img])
                        st.session_state.results = res.text
                        st.success("Đã đọc xong!")
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

        if st.session_state.results:
            raw = st.session_state.results
            st.info(raw)
            rows = []
            # Tìm địa chỉ
            addr_search = re.search(r'ADDRESS:\s*(.*)', raw)
            if addr_search: st.session_state.address = addr_search.group(1).split('\n')[0].strip().replace(" ","_")
            
            # Tìm số đo
            matches = re.findall(r'([^|\n]+?)\s*[|:]?\s*(\d{3,4})\s*[xX*|]\s*(\d{3,4})', raw)
            for m in matches:
                metric, money, unit = calculate_an_tam(m[1], m[2], selected_item)
                rows.append({"Vị trí": m[0].strip(), "Ngang": m[1], "Cao": m[2], "Loại": selected_item, unit: metric, "Tiền($$)": money})
            
            if rows:
                df = pd.DataFrame(rows)
                st.table(df)
                st.success(f"💰 TỔNG CỘNG: ${round(df['Tiền($)'].sum(), 2)}")
                out_ex = BytesIO()
                df.to_excel(out_ex, index=False)
                st.download_button(f"📥 TẢI EXCEL {st.session_state.address}", out_ex.getvalue(), f"{st.session_state.address}.xlsx")

    # --- PHẦN 2: LƯU INVOICE ---
    else:
        st.subheader("🧾 CHỤP VÀ CHUYỂN INVOICE SANG PDF")
        pdf_name = st.text_input("Tên khách hàng:", "Invoice_AnTam")
        inv_img = st.camera_input("CHỤP HÓA ĐƠN")
        if inv_img:
            with st.spinner('Đang tạo PDF...'):
                pdf = FPDF(); pdf.add_page()
                img_p = PIL.Image.open(inv_img); img_p.save("temp.jpg")
                pdf.image("temp.jpg", x=10, y=10, w=190)
                st.download_button("📥 TẢI PDF VỀ MÁY", pdf.output(dest='S').encode('latin-1'), f"{pdf_name}.pdf")
else:
    st.error("Dán mã API vào Secrets đi Jimmy!")
