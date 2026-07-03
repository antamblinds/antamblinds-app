import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - BÁO GIÁ THÔNG MINH")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

# Khởi tạo bộ nhớ tạm để không bị gọi AI nhiều lần (Tiết kiệm hạn mức 429)
if 'results' not in st.session_state:
    st.session_state.results = None
if 'address' not in st.session_state:
    st.session_state.address = "Khach_Hang_An_Tam"

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
    # Lấy model đang sống
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(models[0])

    st.sidebar.title("DANH MỤC")
    selected_item = st.sidebar.selectbox("Chọn rèm:", 
        ["Roller ($60/m2)", "Vertical ($65/m2)", "Shutters ($140/m2)", "Sheer Curtains ($120/m)", "Blockout Curtains ($$145/m)"])
    
    img_file = st.camera_input("CHỤP SỔ ĐO")
    
    if img_file:
        # Nút bấm để kích hoạt AI - CHỈ CHẠY 1 LẦN KHI NHẤN
        if st.button("🚀 BẮT ĐẦU ĐỌC VỚI AI"):
            with st.spinner('Đang đọc... (Nếu gặp lỗi 429, hãy đợi 60 giây)'):
                try:
                    img = PIL.Image.open(img_file)
                    # Yêu cầu AI trả về định dạng chuẩn để dễ tách số
                    prompt = "Read address and sizes. Return format: ADDRESS: [addr] DATA: [Loc | W | H]"
                    res = model.generate_content([prompt, img])
                    
                    st.session_state.results = res.text # Lưu vào bộ nhớ tạm
                    st.success("AI đã đọc xong!")
                except Exception as e:
                    st.error(f"Lỗi AI: {e}. Mẹo: Hãy đợi 1 phút hoặc đổi API Key mới.")

    # Hiển thị kết quả từ bộ nhớ tạm
    if st.session_state.results:
        raw_text = st.session_state.results
        st.info(raw_text)
        
        rows = []
        # Tìm địa chỉ
        addr_match = re.search(r'ADDRESS:\s*(.*)', raw_text)
        if addr_match: st.session_state.address = addr_match.group(1).split('\n')[0].strip().replace(" ","_")

        # Tìm số đo Ngang x Cao
        matches = re.findall(r'([^|\n]+?)\s*[|:]?\s*(\d{3,4})\s*[xX*|]\s*(\d{3,4})', raw_text)
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
        else:
            st.warning("AI đọc được chữ nhưng không thấy bộ số Width x Height. Ông thử chụp rõ hơn nhé!")
else:
    st.error("Dán API Key vào Secrets nha Jimmy!")
