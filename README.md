# 練習專案七：小小停車場

## 簡介

這個專案「小小停車場」透過 `gradio` 與 `easyocr` 模組製作出一個以秒計費的停車場網頁應用程式。我們使用了 `easyocr` 進行車牌辨識，透過 Python 函數與標準模組進行概念驗證，並以 `gradio` 與 `streamlit` 的介面做出成品。

 - `gradio` 可以點選 [Hugging Face Spaces gradio的連結](https://huggingface.co/spaces/namidairo321/parking_lot) 參考成品。
 - `streamlit` 可以點選 [Streamlit Community Cloud的連結](https://parkinglotst.streamlit.app/) 參考成品。

## 如何重現

 - 安裝 [Miniconda](https://docs.anaconda.com/miniconda)
 - 依據 `environment_local.yml` 建立環境：

```bash
 conda env create -f environment_local.yml
```

 - 將 `data/` 資料夾中的 `car_plate_1.jpg`、`car_plate_2.jpg` 與 `car_plate_3.jpg` 放置於專案資料夾的 `data/` 資料夾中。
 - 啟動環境並執行 `python app.py` 並前往 `http://127.0.0.1:7860` 瀏覽成品。
 - 啟動環境並執⾏ `streamlit run app_streamlit.py` 並前往 `http://192.168.1.103:8501` 瀏覽成品。