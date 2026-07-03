import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH HUB
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - CÔNG CỤ HOÀN THIỆN")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

def main():
    if not api_key:
        st.error("Jimmy ơi, dán API Key vào Secrets nha!")
        return

    # TỰ DÒ MODEL AI
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

    if task == "📝 Ghi Sổ Đo -> Excel":
        st.subheader("📝 CHỤP SỔ ĐO (Đọc tất cả các cửa - Xuất Excel)")
        img_file = st.camera_input("CHỤP TỜ GIẤY ĐO", key="cam_sodo")
        
        if img_file:
            with st.spinner('Đang bóc tách toàn bộ sổ đo...'):
                try:
                    img = PIL.Image.open(img_file)
                    # Prompt đơn giản để AI không bị rối, đọc hết mọi thứ nó thấy
                    prompt = "Identify the job address and EVERYTHING on this paper. For each line with numbers like '1234 x 5678', capture the location text before it and any notes like (L) kc after it."
                    res = model.generate_content([prompt, img])
                    raw = res.text
                    
                    st.success("✅ ĐÃ ĐỌC XONG!")
                    st.info(raw) # Để Jimmy coi AI nó đọc thô ra cái gì

                    # 🎯 TÌM ĐỊA CHỈ ĐỂ ĐẶT TÊN FILE
                    f_name = "Khach_Hang_An_Tam"
                    addr_match = re.search(r'(Address|Địa chỉ|Dia chi):\s*(.*)', raw, re.IGNORECASE)
                    if addr_match:
                        f_name = addr_match.group(2).split('\n')[0].strip().replace(" ","_").replace(",","")
                    
                    # 🎯 BỘ QUÉT SỐ "SIÊU ĐA NĂNG" - QUÉT HẾT MỌI DÒNG CÓ SỐ
                    rows = []
                    lines = raw.split('\n')
                    for line in lines:
                        # Tìm bộ số Ngang x Cao (3-4 chữ số)
                        match = re.search(r'(\d{3,4})\s*[xX*/-]\s*(\d{3,4})', line)
                        if match:
                            w = match.group(1)
                            h = match.group(2)
                            
                            # Lấy chữ đằng trước làm Vị trí
                            loc_part = line.split(match.group(0))[0].strip().replace("-","").replace(".","")
                            # Lấy chữ đằng sau làm Ghi chú (L, R, kc...)
                            note_part = line.split(match.group(0))[1].strip().replace("(","").replace(")","").replace(" ","")
                            
                            # ĐỊNH DẠNG CHUẨN JIMMY: 1525/1458.Lkc
                            jimmy_format = f"{w}/{h}"
                            if note_part:
                                jimmy_format += f".{note_part}"
                            
                            rows.append({
                                "Vị trí": loc_part if loc_part else "Cửa chính",
                                "Kích thước (Copy)": jimmy_format
                            })
                    
                    if rows:
                        df = pd.DataFrame(rows)
                        st.table(df) # Hiện bảng đầy đủ các cửa
                        
                        out_ex = BytesIO()
                        with pd.ExcelWriter(out_ex, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        
                        st.download_button(
                            label=f"📥 TẢI EXCEL: {f_name}.xlsx",
                            data=out_ex.getvalue(),
                            file_name=f"{f_name}.xlsx"
                        )
                    else:
                        st.warning("AI thấy hình nhưng không lọc được số đo. Ông thử chụp gần lại nhé!")

                except Exception as ex:
                    st.error(f"Lỗi: {ex}")

    else: # PHẦN INVOICE PDF
        st.subheader("🧾 CHỤP INVOICE (Xuất PDF)")
        pdf_n = st.text_input("Ghi địa chỉ/tên khách:", "Invoice_AnTam")
        inv_img = st.camera_input("CHỤP HÓA ĐƠN", key="cam_inv")
        if inv_img:
            pdf = FPDF(); pdf.add_page()
            img_p = PIL.Image.open(inv_img); img_p.save("temp.jpg")
            pdf.image("temp.jpg", x=10, y=10, w=190)
            st.download_button(f"📥 TẢI PDF: {pdf_n}.pdf", pdf.output(dest='S').encode('latin-1'), f"{pdf_n}.pdf")

if __name__ == "__main__":
    main()
