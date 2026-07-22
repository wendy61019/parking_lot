import streamlit as st
import sqlite3
import re
import pytesseract
from PIL import Image
from PIL import ImageEnhance
from PIL import ImageOps
from datetime import datetime
from datetime import timezone
from datetime import timedelta

#建立SQL資料庫
parking_db = "parking.db"

#建立當前時間函式
TIMEZONE_TW = timezone(timedelta(hours=8))
def get_current_time():
    return datetime.now(TIMEZONE_TW)

@st.cache_resource
#初始化資料庫，建立車輛紀錄表
#建立一個資料表 欄位有：車牌(主鍵)與進場時間
def create_parking_db():
    with sqlite3.connect(parking_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS parking_records(
                car_plate TEXT PRIMARY KEY,
                entry_time TEXT NOT NULL
            )
            """
            )
        conn.commit()

#取得目前所有場內車輛
def get_all_parked_vehicles():
    with sqlite3.connect(parking_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT car_plate, entry_time FROM parking_records ORDER BY entry_time DESC"
        )
        return cursor.fetchall()

#車輛辨識與進出場判讀
def process_parking(car_plate: str ,ntd_per_sec: int):
    now = get_current_time()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(parking_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT entry_time FROM parking_records WHERE car_plate = ?",
            (car_plate,),
        )
        result = cursor.fetchone()
#新增車輛進場紀錄
        if result is None:
            cursor.execute(
                "INSERT OR REPLACE INTO parking_records (car_plate, entry_time) VALUES (?, ?)",
            (car_plate, now_str)
            )
            conn.commit()
            return "ENTRY", {
                "car_plate": car_plate,
                "entry_time_str": now_str,
                "ntd_per_sec": ntd_per_sec,
            }
        else:
            entry_time_str = result[0]
            entry_time = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TIMEZONE_TW)
            time_elapsed = now - entry_time
            seconds_elapsed = max(0, int(time_elapsed.total_seconds()))
            charged_amount = seconds_elapsed * ntd_per_sec
##刪除車輛出場紀錄
            cursor.execute(
                "DELETE FROM parking_records WHERE car_plate = ?", (car_plate,)
            )
            conn.commit()
            return "EXIT", {
                "car_plate": car_plate,
                "seconds_elapsed": seconds_elapsed,
                "charged_amount": charged_amount,
            }

#影像預處理函式
def preprocess_img_for_ocr(pil_img):
#轉灰階
    gray = pil_img.convert("L")
#自動調整對比度
    gray = ImageOps.autocontrast(gray)    
#提高對比度
    enhancer = ImageEnhance.Contrast(gray)
    enhanced_img = enhancer.enhance(2.0)
    return enhanced_img

#啟動資料庫初始化
create_parking_db()

#設定網頁標題與排版
st.set_page_config(page_title="小小停車場", page_icon="🚗", layout="wide")
st.title("🚗 小小停車場")

#建立側邊欄
st.sidebar.header("設定參數")
ntd_per_sec = st.sidebar.number_input(
    "每秒收費 (NTD)", min_value=1, value=1, step=1
)
uploaded_img = st.file_uploader(
    "請上傳車牌照片", type=["jpg", "jpeg", "png"]
)

#車輛辨識與映射到UI
#在UI建立2欄式版面
if uploaded_img is not None:
    col1, col2 = st.columns([1, 1], gap="medium")
    image = Image.open(uploaded_img).convert("RGB")
    with col1:
        st.subheader("📷 上傳照片")
        st.image(image, caption="已上傳的照片", width="stretch")
    with col2:
        if st.button("進行車牌辨識與結算", type="primary"):
            with st.spinner("辨識中..."):
                preprocessed_image = preprocess_img_for_ocr(image)
                custom_config = r"--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
                image_text = pytesseract.image_to_string(image, lang="eng", config=custom_config)
                car_plate = re.sub(r"[^A-Z0-9-]", "", image_text.upper().strip())
                if not car_plate:
                    st.error("❌ 無法辨識車牌，請重新上傳清晰的照片！")
                else:
                    action_type, data = process_parking(car_plate, ntd_per_sec)
                    if action_type == "ENTRY":
                        st.success(f"👋 **Welcome to the parking lot, {data['car_plate']}!**")
                        st.info(
                            f"🕒 Entry Time：{data['entry_time_str']}\n\n"
                            f"💰 Parking Rates：Per Sec NT${data['ntd_per_sec']}"
                        )
                    elif action_type == "EXIT":
                        st.balloons()
                        st.success(f"👋 **Bye bye bye, {data['car_plate']}!**")
                        st.warning(
                            f"⏱️ Your vehicle stayed： {data['seconds_elapsed']} secs.\n\n"
                            f"💵 You will be charged NT${data['charged_amount']:,}."
                        )

#查詢場內車輛並即時顯示側邊欄
st.sidebar.markdown("---")
st.sidebar.subheader("🅿️ 目前場內車輛")

parked_list = get_all_parked_vehicles()
if parked_list:
    now = get_current_time()
    for car_plate, entry_str in parked_list:
        entry_dt = datetime.strptime(entry_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TIMEZONE_TW)
        stayed_secs = max(0, int((now - entry_dt).total_seconds()))
        st.sidebar.markdown(f"🚘 {car_plate} \n"
                        f"🕒 Entry: `{entry_str[11:]}` (For {stayed_secs} secs.)")
else:
    st.sidebar.caption("No vehicles in the parking lot.")