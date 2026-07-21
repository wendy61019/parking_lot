import gradio as gr
import easyocr
from datetime import datetime
from datetime import timezone
from datetime import timedelta

reader = easyocr.Reader(["en"], gpu=True)
parked_vehicles = dict()

#定義 parking_lot_ocr() 函數
def parking_lot_ocr(uploaded_img, ntd_per_sec: int = 1):
    results = reader.readtext(uploaded_img, detail=0)
    entry_time = datetime.now(timezone.utc) + timedelta(hours=8)
    entry_time_str = entry_time.strftime("%Y-%m-%d %H:%M:%S")
    car_plate = results[0]
    if car_plate not in parked_vehicles.keys():
        parked_vehicles[car_plate] = entry_time
        output_message = f"""
        Welcome to the parking lot {car_plate}!\n
        Your entry time is: {entry_time_str}.\n
        Parking fee is NT${ntd_per_sec} per second.
        """
        return output_message
    else:
        leaving_time = datetime.now(timezone.utc) + timedelta(hours=8)
        time_elapsed = leaving_time - parked_vehicles[car_plate]
        seconds_elapsed = int(time_elapsed.total_seconds())
        charge_amount = seconds_elapsed * ntd_per_sec
        parked_vehicles.pop(car_plate, None)
        output_message = f"""
        Bye bye bye {car_plate}!\n
        Your vehicle stayed {seconds_elapsed} seconds.\n
        You will be charged NT${charge_amount:,}.
        """
        return output_message

demo = gr.Interface(fn=parking_lot_ocr,
                    inputs=gr.Image(),
                    outputs="text",
                    title="小小停車場")

demo.launch()