import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH HUB
st.set_page_config(page_title="An Tam Blinds Master", layout="wide")
st.header("🏠 AN TAM BLINDS - HỆ THỐNG HOÀN THIỆN")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

def main():
    if not api_key:
        st.error("Dán API Key vào Secrets đi Jimmy ơi!")
        return

    # TỰ DÒ AI (TRỊ LỖI 404)
    try:
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_id = next((m for m in models if 'flash' in m.lower()), models[0])
        model = genai.GenerativeModel(model_id)
    except Exception as e:
        st.error(f"Lỗi AI: {e}")
        return

    st.sidebar.title("DANH MỤC")
    task = st.sidebar.radio("CHỌN VIỆC:", ["📝 Ghi Sổ Đo -> Excel", "🧾 Lưu Invoice -> PDF"])

    # --- PHẦN 1: GHI SỔ ĐO (GIỐNG HỆT BẢN ÔNG KHEN TỐT) ---
    if task == "📝 Ghi Sổ Đo -> Excel":
        st.subheader("📝 CHỤP SỔ ĐO (Excel theo địa chỉ khách)")
        img_file = st.camera_input("CHỤP TỜ GIẤY ĐO", key="cam_sodo")
        
        if img_file:
            if st.button("🚀 XÁC NHẬN ĐỌC SỔ ĐO"):
                with st.spinner('AI đang bóc tách số liệu...'):
                    try:
                        img = PIL.Image.open(img_file)
                        prompt = "Identify address and EVERY measurement. Format: ADDRESS: [addr] DATA: [Location | Width | Height | Notes]"
                        res = model.generate_content([prompt, img])
                        raw = res.text
                        st.success("✅ ĐÃ ĐỌC XONG!")
                        st.info(raw)

                        # TÌM ĐỊA CHỈ ĐẶT TÊN FILE
                        f_name = "Khach_An_Tam"
                        addr_match = re.search(r'(ADDRESS:|Địa chỉ:|Dia chi:)\s*(.*)', raw, re.IGNORECASE)
                        if addr_match:
                            f_name = addr_match.group(2).split('\n')[0].strip().replace(" ","_").replace(",","")

                        # TẠO BẢNG CÓ DIỆN TÍCH (Giống mẫu ông thích)
                        rows = []
                        lines = raw.split('\n')
                        don_gia = 100 
                        for line in lines:
                            match = re.search(r'(\d{3,4})\s*[xX*/-]\s*(\d{3,4})', line)
                            if match:
                                w = int(match.group(1)); h = int(match.group(2))
                                loc = line.split(match.group(0))[0].strip().replace("-","").replace(".","")
                                nt = line.split(match.group(0))[1].strip().replace("(","").replace(")","").replace(" ","")
                                
                                dt_thuc = round((w/1000)*(h/1000), 2)
                                dt_tinh = max(dt_thuc, 1.5)
                                rows.append({
                                    "Vị trí": loc if loc else "Cửa",
                                    "Rộng (mm)": w, "Cao (mm)": h,
                                    "Kích thước gốc": f"{w}/{h}.{nt}",
                                    "Diện tích thực": dt_thuc,
                                    "Diện tích tính tiền": dt_tinh,
                                    "Thành tiền": round(dt_tinh * don_gia, 2),
                                    "Ghi chú": nt
                                })
                        
                        if rows:
                            df = pd.DataFrame(rows)
                            st.table(df)
                            out_ex = BytesIO()
                            with pd.ExcelWriter(out_ex, engine='openpyxl') as writer:
                                df.to_excel(writer, index=False)
                            st.download_button(f"📥 TẢI EXCEL: {f_name}.xlsx", out_ex.getvalue(), f"{f_name}.xlsx")
                    except Exception as ex: st.error(f"Lỗi: {ex}")

    # --- PHẦN 2: LƯU INVOICE (SỬA LỖI TỰ QUÉT TÊN CÔNG TY) ---
    else:
        st.subheader("🧾 CHỤP INVOICE (Tự quét tên Nhà cung cấp)")
        inv_img = st.camera_input("CHỤP HÓA ĐƠN", key="cam_inv")
        if inv_img:
            if st.button("🚀 BẮT ĐẦU QUÉT TÊN CÔNG TY"):
                with st.spinner('Đang nhận diện...'):
                    try:
                        img_p = PIL.Image.open(inv_img)
                        # Ép AI tìm tên công ty cung cấp
                        res_inv = model.generate_content(["Extract ONLY the supplier or company name from this receipt. Be very brief.", img_p])
                        supplier = res_inv.text.strip().replace(" ","_").replace(".","").replace("/","").split('\n')[0]
                        if not supplier or len(supplier) > 30: supplier = "Invoice_AnTam"

                        st.success(f"✅ Đã nhận diện: {supplier}")
                        
                        pdf = FPDF(); pdf.add_page()
                        img_p.save("temp.jpg")
                        pdf.image("temp.jpg", x=10, y=10, w=190)
                        st.download_button(f"📥 TẢI PDF: {supplier}.pdf", pdf.output(dest='S').encode('latin-1'), f"{supplier}.pdf")
                    except Exception as e_pdf: st.error(f"Lỗi PDF: {e_pdf}")

if __name__ == "__main__":
    main()
