import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - CÔNG CỤ TỰ ĐỘNG THÔNG MINH")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

def main():
    if not api_key:
        st.error("Jimmy ơi, dán API Key vào Secrets nhé!")
        return

    # --- HÀM TÌM AI AN TOÀN (TRỊ LỖI 404) ---
    try:
        genai.configure(api_key=api_key)
        # Tự động tìm model Flash khả dụng bất kể phiên bản nào
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in models if 'flash' in m.lower()), models[0])
        model = genai.GenerativeModel(target_model)
    except Exception as e_ai:
        st.error(f"Lỗi AI: {e_ai}. Jimmy thử tạo API Key mới xem sao nha.")
        return

    st.sidebar.title("DANH MỤC")
    task = st.sidebar.radio("CHỌN VIỆC:", ["📝 Ghi Số Đo -> Excel", "🧾 Lưu Invoice -> PDF"])

    # --- PHẦN 1: GHI SỔ ĐO (EXCEL CHUẨN MẪU) ---
    if task == "📝 Ghi Sổ Đo -> Excel":
        st.subheader("📝 CHỤP SỔ ĐO (Tự động tính Diện tích & Đặt tên Địa chỉ)")
        img_file = st.camera_input("CHỤP TỜ GIẤY ĐO", key="cam_sodo")
        
        if img_file:
            with st.spinner('Đang đọc sổ đo và tính tiền...'):
                try:
                    img = PIL.Image.open(img_file)
                    prompt = "Identify address and measurements. Return exactly: ADDRESS: [addr] DATA: [Location | Width | Height | Notes]"
                    res = model.generate_content([prompt, img])
                    raw = res.text
                    
                    # 🎯 BẮT ĐỊA CHỈ LÀM TÊN FILE
                    f_name = "Khach_An_Tam"
                    addr_match = re.search(r'(Address:|Địa chỉ:|Dia chi:|ADDRESS:)\s*(.*)', raw, re.IGNORECASE)
                    if addr_match:
                        f_name = addr_match.group(2).split('\n')[0].strip().replace(" ","_").replace(",","").replace(".","")

                    rows = []
                    lines = raw.split('\n')
                    don_gia = 100 # Đơn giá mặc định, ông có thể sửa

                    for line in lines:
                        match = re.search(r'(\d{3,4})\s*[xX*/-]\s*(\d{3,4})', line)
                        if match:
                            w = int(match.group(1)); h = int(match.group(2))
                            loc = line.split(match.group(0))[0].strip().replace("-","").replace(".","")
                            notes = line.split(match.group(0))[1].strip().replace("(","").replace(")","").replace(" ","")
                            
                            # Tính diện tích & Thành tiền (Theo mẫu Jimmy ưng)
                            dt_thuc = round((w/1000)*(h/1000), 2)
                            dt_tinh = max(dt_thuc, 1.5)
                            total = round(dt_tinh * don_gia, 2)
                            
                            rows.append({
                                "Vị trí": loc if loc else "Cửa",
                                "Rộng (mm)": w,
                                "Cao (mm)": h,
                                "Kích thước gốc": f"{w}/{h}.{notes}",
                                "Diện tích thực": dt_thuc,
                                "Diện tích tính tiền": dt_tinh,
                                "Đơn giá": don_gia,
                                "Thành tiền": total,
                                "Ghi chú": notes
                            })
                    
                    if rows:
                        df = pd.DataFrame(rows)
                        st.table(df)
                        out_ex = BytesIO()
                        with pd.ExcelWriter(out_ex, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        st.download_button(f"📥 TẢI EXCEL: {f_name}.xlsx", out_ex.getvalue(), f"{f_name}.xlsx")
                    else:
                        st.warning("AI không đọc được số đo, ông chụp cận cảnh tí nha!")
                except Exception as e: st.error(f"Lỗi: {e}")

    # --- PHẦN 2: LƯU INVOICE (TỰ ĐẶT TÊN THEO CÔNG TY/NHÀ CUNG CẤP) ---
    else:
        st.subheader("🧾 CHỤP INVOICE (AI tự quét tên Nhà cung cấp để đặt tên file)")
        inv_img = st.camera_input("CHỤP HÓA ĐƠN", key="cam_inv")
        
        if inv_img:
            with st.spinner('AI đang tìm tên Nhà cung cấp trên hình...'):
                try:
                    img = PIL.Image.open(inv_img)
                    # Yêu cầu AI tìm tên công ty in trên hóa đơn
                    res_inv = model.generate_content(["Find the Supplier or Company Name on this invoice only. Be extremely brief.", img])
                    supplier = res_inv.text.strip().replace(" ","_").replace(".","").split('\n')[0]
                    
                    if not supplier or len(supplier) > 30:
                        supplier = "Invoice_AnTam"
                    
                    st.success(f"✅ Đã nhận diện Nhà cung cấp: {supplier}")
                    
                    # TẠO PDF
                    pdf = FPDF(); pdf.add_page()
                    img.save("invoice_temp.jpg")
                    pdf.image("invoice_temp.jpg", x=10, y=10, w=190)
                    st.download_button(f"📥 TẢI PDF: {supplier}.pdf", pdf.output(dest='S').encode('latin-1'), f"{supplier}.pdf")
                except Exception as e_pdf: st.error(f"Lỗi PDF: {e_pdf}")

if __name__ == "__main__":
    main()
