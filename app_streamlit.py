import sqlite3
import re
import cv2
import numpy as np
import pytesseract
import streamlit as st
from datetime import datetime
from datetime import timedelta
from datetime import timezone

# ==========================================
# 建立資料庫模組(Database Management)
# ==========================================
parking_db = "parking_lot.db"

#初始化 SQLite 資料庫與資料表
def init_db():
    with sqlite3.connect(parking_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                car_plate TEXT PRIMARY KEY,
                entry_time TEXT NOT NULL
            )
            """
        )
        conn.commit()

#查詢車輛進場紀錄
def get_parked_vehicle(car_plate: str):
    with sqlite3.connect(parking_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT entry_time FROM records WHERE car_plate = ?", (car_plate,)
        )
        result = cursor.fetchone()
        return result[0] if result else None

#新增進場車輛
def add_parked_vehicle(car_plate: str, entry_time_str: str):
    with sqlite3.connect(parking_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO records (car_plate, entry_time) VALUES (?, ?)",
            (car_plate, entry_time_str),
        )
        conn.commit()

#刪除出場車輛紀錄
def remove_parked_vehicle(car_plate: str):
    with sqlite3.connect(parking_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM records WHERE car_plate = ?", (car_plate,)
        )
        conn.commit()

# ==========================================
# 影像預處理與 OCR 模組(Vision & OCR)
# ==========================================
#使用 OpenCV 進行影像預處理
def preprocess_image(image_bytes: bytes) -> np.ndarray:
#將上傳的 bytes 轉為 OpenCV 格式(BGR)
    file_bytes = np.asarray(bytearray(image_bytes), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Unable to read image file.")
#轉灰階
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#雙邊濾波（去除雜訊但保留邊緣）
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)
#Otsu 二值化
    ret, thresh = cv2.threshold(
        filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return thresh

#使用 Tesseract 進行 OCR 辨識
def extract_plate_text(processed_img: np.ndarray) -> str:
    if np.mean(processed_img) < 127:
        processed_img = cv2.bitwise_not(processed_img)
    custom_config = r"--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    raw_text = pytesseract.image_to_string(processed_img, config=custom_config)
#清理文字：僅保留英數字，轉大寫
    clean_text = re.sub(r"[^A-Z0-9]", "", raw_text.upper())
    return clean_text

# ==========================================
# 車輛進出場邏輯與費用計算(Business Logic)
# ==========================================
def process_parking_event(car_plate: str, rate_per_sec: int):
# 取得當前時間 (UTC+8)
    tz_utc8 = timezone(timedelta(hours=8))
    now = datetime.now(tz_utc8).replace(tzinfo=None)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    entry_time_str = get_parked_vehicle(car_plate)
    if entry_time_str is None:
#進場流程
        add_parked_vehicle(car_plate, now_str)
        return {
            "status": "ENTRY",
            "message": f"🚗 【Entry Success!】\n\n- Car Plate：`{car_plate}`\n- Entry Time：`{now_str}`\n- Rates：`NT${rate_per_sec} / sec.`",
        }
    else:
#出場流程
        entry_time = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")
        time_elapsed = now - entry_time
        seconds_elapsed = max(int(time_elapsed.total_seconds()), 1)
        charge_amount = seconds_elapsed * rate_per_sec
#離場時移除紀錄
        remove_parked_vehicle(car_plate)
        return {
            "status": "EXIT",
            "message": f"💳 【EXIT SUCCESS!】\n\n- Car Plate：`{car_plate}`\n- Exit Time：`{now_str}`\n- Time Parked：`{seconds_elapsed} sec.`\n- Amount Due：`NT${charge_amount:,}`.",
        }

# ==========================================
# Streamlit UI 介面
# ==========================================
#建立streamlit
def main():
    st.set_page_config(
        page_title="小小停車場", page_icon="🅿️", layout="wide"
    )

#初始化資料庫
    init_db()

    st.title("🅿️ 小小停車場")
#建立側邊欄
    st.sidebar.header("⚙️ Parking System Settings")
    rate_per_sec = st.sidebar.slider(
        "Rate Per Sec (NTD)", min_value=1, max_value=200, value=1
    )
#建立2欄頁面
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📸 車牌辨識區")
        uploaded_file = st.file_uploader(
            "請上傳車牌照片", type=["jpg", "jpeg", "png"]
        )
        if uploaded_file is not None:
            image_bytes = uploaded_file.read()
            processed_img = preprocess_image(image_bytes)
            #顯示原始照片
            st.image(processed_img, caption="OpenCV預處理結果", width="stretch")
            #按鈕觸發辨識
            if st.button("🚀 進行車牌辨識", type="primary"):
                car_plate = extract_plate_text(processed_img)
                #st.write(f"🔍 OCR 抓到的字串：'{car_plate}'")
                if not car_plate or len(car_plate) < 3:
                    st.error("❌ 無法辨識出有效車牌，請上傳更清晰的照片！")
                else:
                    result = process_parking_event(car_plate, rate_per_sec)
                    st.markdown(result["message"])
    with col2:
        st.subheader("📋 目前場內車輛清單")
        if st.button("🔄 刷新清單"):
            st.rerun()

#讀取並顯示SQLite內的資料
        with sqlite3.connect(parking_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT car_plate, entry_time FROM records")
            rows = cursor.fetchall()
            if rows:
                st.table(
                    [
                        {"Car Plate": row[0], "Entry Time": row[1]}
                        for row in rows
                    ]
                )
            else:
                st.write("Parking lot is empty.")

if __name__ == "__main__":
    main()