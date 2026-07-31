import sqlite3
import easyocr
import numpy as np
import streamlit as st
from PIL import Image
from datetime import datetime
from datetime import timedelta
from datetime import timezone

#建立streamlit介面
st.set_page_config(page_title="小小停車場", page_icon="🚗")
st.title("🚗 小小停車場")

parking_db = "parking.db"


#初始化 EasyOCR 模型快取
@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(["en"], gpu=True)
reader = load_ocr_reader()


#初始化 SQLite 資料庫
def init_db():
    conn = sqlite3.connect(parking_db)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS parked_vehicles (
            car_plate TEXT PRIMARY KEY,
            entry_time TEXT
        )
    """
    )
    conn.commit()
    conn.close()

init_db()

#先建立場內是否有車輛
def get_entry_time(car_plate: str):
    conn = sqlite3.connect(parking_db)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT entry_time FROM parked_vehicles WHERE car_plate = ?",
        (car_plate,),
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

#新增進場車輛
def add_vehicle(car_plate: str, entry_time_str: str):
    conn = sqlite3.connect(parking_db)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO parked_vehicles (car_plate, entry_time) VALUES (?, ?)",
        (car_plate, entry_time_str),
    )
    conn.commit()
    conn.close()

#移除出場車輛
def remove_vehicle(car_plate: str):
    conn = sqlite3.connect(parking_db)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM parked_vehicles WHERE car_plate = ?", (car_plate,)
    )
    conn.commit()
    conn.close()


def get_all_parked_vehicles():
    conn = sqlite3.connect(parking_db)
    cursor = conn.cursor()
    cursor.execute("SELECT car_plate, entry_time FROM parked_vehicles")
    rows = cursor.fetchall()
    conn.close()
    return rows


#建立側邊欄控制與參數
st.sidebar.header("⚙️ 費率與設定")
ntd_per_sec = st.sidebar.number_input(
    "Rate Per Sec (NT$)", min_value=1, value=1, step=1
)

#主介面
uploaded_file = st.file_uploader(
    "請上傳車牌照片...", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    # 顯示圖片
    image = Image.open(uploaded_file)
    st.image(image, caption="上傳的照片")

    # 轉成 EasyOCR 支援格式
    img_array = np.array(image)

    with st.spinner("車牌辨識中..."):
        results = reader.readtext(img_array, detail=0)

    if not results:
        st.error("❌ 無法辨識車牌，請上傳更清晰的照片。")
    else:
        car_plate = results[0]
        entry_time = datetime.now(timezone.utc) + timedelta(hours=8)
        entry_time_str = entry_time.strftime("%Y-%m-%d %H:%M:%S")
        existing_entry_time_str = get_entry_time(car_plate)

        #車輛入場邏輯
        if existing_entry_time_str is None:
            add_vehicle(car_plate, entry_time_str)
            st.success(f"🎉 Welcome！Car Plate：**{car_plate}**")
            st.info(
                f"""
                - **Entry Time**：{entry_time_str}
                - **Parking Rates**：NT$ {ntd_per_sec} / sec.
            """
            )
        #車輛出場邏輯
        else:
            leaving_time = datetime.now(timezone.utc) + timedelta(hours=8)
            leaving_time_dt = leaving_time.replace(tzinfo=None)
            entry_dt = datetime.strptime(existing_entry_time_str, "%Y-%m-%d %H:%M:%S")
            time_elapsed = leaving_time_dt - entry_dt
            seconds_elapsed = int(time_elapsed.total_seconds())
            charge_amount = seconds_elapsed * ntd_per_sec

            remove_vehicle(car_plate)

            st.warning(f"Bye Bye Bye！Car Plate：**{car_plate}**")
            st.write(
                f"""
                - **Parked Time**：{seconds_elapsed} sec.
                - **Charged Amount**：**NT$ {charge_amount:,}**
            """
            )


#顯示目前停放車輛名單
st.markdown("---")
st.subheader("🅿️ 目前停放中的車輛紀錄")

parked_list = get_all_parked_vehicles()
if parked_list:
    st.table(
        [
            {"Car Plate": row[0], "Entry Time": row[1]}
            for row in parked_list
        ]
    )
else:
    st.write("There are no cars in the parking lot.")