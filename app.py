import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH HUB
st.set_page_config(page_title="An Tam Blinds Master", layout="wide")
st.header("🏠 AN TAM BLINDS - CÔNG CỤ HOÀN THIỆN")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

def main():
    if not api_key:
        st.error("Jimmy ơi, dán API Key vào Secrets nha!")
        return

    # TỰ DÒ AI (TRỊ LỖI 404)
    try:
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_id = next((m for m in available_models if 'flash' in m.lower()), available_models[0])
        model = genai.GenerativeModel(model_id)
    except Exception as e:
        st.error(f"Lỗi AI: {e}")
        return

    st.sidebar.title("DANH MỤC")
    task = st.sidebar.radio("CHỌN VIỆC:", ["📝 Ghi Sổ Đo -> Excel", "🧾 Lưu Invoice -> PDF"])

    # --- PHẦN 1: GHI SỔ ĐO (GIỮ NGUYÊN BẢN GỐC ÔNG ƯNG Ý) ---
    if task == "📝 Ghi Sổ Đo -> Excel":
        st.subheader("📝 CHỤP SỔ ĐO (Excel theo địa chỉ khách)")
        img_file = st.camera_input("CHỤP TỜ GIẤY ĐO", key="cam_sodo")
        
        if img_file:
            with st.spinner('AI đang bóc tách số liệu...'):
                try:
                    img = PIL.Image.open(img_file)
                    # Prompt ông dùng thấy ổn nhất
                    prompt = "Identify the job address and EVERY measurement. Format: ADDRESS: [addr] then list each door with its Width x Height and notes."
                    res = model.generate_content([prompt, img])
                    raw = res.text
                    
                    st.success("✅ ĐÃ ĐỌC XONG!")
                    st.info(raw)

                    # TÌM ĐỊA CHỈ ĐẶT TÊN FILE
                    f_name = "Khach_An_Tam"
                    addr_match = re.search(r'(ADDRESS:|Địa chỉ:|Dia chi:)\s*(.*)', raw, re.IGNORECASE)
                    if addr_match:
                        f_name = addr_match.group(2).split('\n')[0].strip().replace(" ","_").replace(",","").replace(".","")
                    
                    # BỘ QUÉT SỐ ĐA NĂNG (Đọc đủ nhiều cửa)
                    rows = []
                    lines = raw.split('\n')
                    for line in lines:
                        match = re.search(r'(\d{3,4})\s*[xX*/-]\s*(\d{3,4})', line)
                        if match:
                            w = match.group(1); h = match.group(2)
                            loc_part = line.split(match.group(0))[0].strip().replace("-","").replace(".","")
                            note_part = line.split(match.group(0))[1].strip().replace("(","").replace(")","").replace(" ","")
                            
                            # Format chuẩn Jimmy: 1525/1458.Lkc
                            jimmy_format = f"{w}/{h}"
                            if note_part:
                                jimmy_format += f".{note_part}"
                            
                            rows.append({
                                "Vị trí": loc_part if loc_part else "Cửa",
                                "Kích thước (Copy)": jimmy_format
                            })
                    
                    if rows:
                        df = pd.DataFrame(rows)
                        st.table(df) 
                        out_ex = BytesIO()
                        with pd.ExcelWriter(out_ex, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        st.download_button(label=f"📥 TẢI EXCEL: {f_name}.xlsx", data=out_ex.getvalue(), file_name=f"{f_name}.xlsx")
                except Exception as ex: st.error(f"Lỗi: {ex}")

    # --- PHẦN 2: LƯU INVOICE (TỰ QUÉT TÊN CÔNG TY) ---
    else:
        st.subheader("🧾 CHỤP INVOICE (Tự đặt tên theo Nhà cung cấp)")
        inv_img = st.camera_input("CHỤP HÓA ĐƠN", key="cam_inv")
        if inv_img:
            with st.spinner('Đang nhận diện Công ty cung cấp...'):
                try:
                    img_p = PIL.Image.open(inv_img)
                    # AI tự soi tên công ty trên hóa đơn
                    res_inv = model.generate_content(["Find the firm or company name on this invoice. Just the name, be brief.", img_p])
                    supplier = res_inv.text.strip().replace(" ","_").replace(".","").split('\n')[0]
                    if not supplier or len(supplier) > 30: 
                        supplier = "Invoice_AnTam"

                    st.success(f"✅ Đã nhận diện: {supplier}")
                    
                    # Xuất PDF
                    pdf = FPDF(); pdf.add_page()
                    img_p.save("temp.jpg")
                    pdf.image("temp.jpg", x=10, y=10, w=190)
                    st.download_button(label=f"📥 TẢI PDF: {supplier}.pdf", data=pdf.output(dest='S').encode('latin-1'), file_name=f"{supplier}.pdf")
                except Exception as e_pdf: st.error(f"Lỗi PDF: {e_pdf}")

if __name__ == "__main__":
    main()
