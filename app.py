
import streamlit as st
import pandas as pd
from openai import OpenAI
import json
#Giao diện cho iPhone
st.set_page_config(page_title="An Tam Blinds Admin", layout="centered")
st.title("🛠 An Tam Blinds v1")
Thanh menu bên trái
with st.sidebar:
st.header("Cài đặt")
api_key = st.text_input("Dán OpenAI API Key của Jimmy vào đây:", type="password")
dist_home = "24 Knight St, Lansvale NSW 2166"
if not api_key:
st.warning(" Jimmy ơi, hãy dán API Key vào thanh menu bên trái để bắt đầu nhé!")
else:
client = OpenAI(api_key=api_key)
option = st.radio("Chọn loại tài liệu:", ["Sổ đo công trình", "Hóa đơn Supplier"])
uploaded_file = st.camera_input("Chụp ảnh ngay")
if uploaded_file:
with st.spinner('Đang đọc dữ liệu...'):
import base64
base64_image = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
prompt = (
"Bạn là thư ký cho An Tam Blinds. Đọc ảnh và trả về JSON. "
"Nếu là sổ đo, tìm: Address, Dimensions (dạng W/H.lkc), L_R (Trái/Phải), Fabric, Notes. "
"Nếu là hóa đơn, tìm: Supplier, TotalAmount, GST, Date. "
"Tất cả bằng tiếng Việt."
)
response = client.chat.completions.create(
model="gpt-4o",
messages=[
{
"role": "user",
"content": [
{"type": "text", "text": prompt},
{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
],
}
],
response_format={ "type": "json_object" }
)
res_data = json.loads(response.choices[0].message.content)
st.subheader("Kết quả AI đọc được:")
final_data = {}
for key, value in res_data.items():
final_data[key] = st.text_input(f"{key}:", value)
if st.button("Lưu & Xuất File"):
df = pd.DataFrame([final_data])
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("Tải File Excel về iPhone", data=csv, file_name="AnTam_Data.csv", mime='text/csv')
st.success("Đã hoàn thành! Bạn có thể mở file bằng Excel trên iPhone.")
