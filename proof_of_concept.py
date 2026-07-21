import easyocr
from datetime import datetime
from datetime import timezone
from datetime import timedelta

reader = easyocr.Reader(["en"], gpu=False)
parked_vehicles = dict()

def parking_lot_ocr(img_path: str, ntd_per_sec: int = 1):
    results = reader.readtext(img_path, detail=0)
    entry_time = datetime.now(timezone.utc) + timedelta(hours=8)
    entry_time_str = entry_time.strftime("%Y-%m-%d %H:%M:%S")
    car_plate = results[0]
    if car_plate not in parked_vehicles.keys():
        parked_vehicles[car_plate] = entry_time
        print(f"Welcome to the parking lot {car_plate}!")
        print(f"Your entry time is: {entry_time_str}.")
        print(f"Parking fee is NT${ntd_per_sec} per second.")
    else:
        leaving_time = datetime.now(timezone.utc) + timedelta(hours=8)
        time_elapsed = leaving_time - parked_vehicles[car_plate]
        seconds_elapsed = int(time_elapsed.total_seconds())
        charge_amount = seconds_elapsed * ntd_per_sec
        print(f"Bye bye bye {car_plate}!")
        print(f"Your vehicle stayed {seconds_elapsed} seconds.")
        print(f"You will be charged NT${charge_amount:,}.")
        parked_vehicles.pop(car_plate, None)

parking_lot_ocr("data/car_plate_1.jpg")
print(parked_vehicles)
parking_lot_ocr("data/car_plate_1.jpg")
print(parked_vehicles)