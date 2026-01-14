import streamlit as st
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas
from io import BytesIO

# --- 1. 頁面基礎設定 ---
st.set_page_config(page_title="方塊去背 (重製版)", layout="wide")
st.title("🔲 Vibe Coding: 方塊去背 (紅框挖/綠框補)")

# --- 2. 上傳圖片 ---
uploaded_file = st.file_uploader("請上傳圖片 (JPG/PNG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # A. 讀取原始高清圖 (這是最後要下載用的)
    # convert("RGBA") 確保它有透明色版
    original_image = Image.open(uploaded_file).convert("RGBA")
    orig_w, orig_h = original_image.size

    # B. 製作畫布用的「縮圖」 (這是給瀏覽器顯示用的)
    # 限制寬度 800px，避免瀏覽器卡死
    display_width = 800
    if orig_w > display_width:
        scale_factor = orig_w / display_width
        display_height = int(orig_h / scale_factor)
        display_image = original_image.resize((display_width, display_height))
    else:
        scale_factor = 1.0
        display_height = orig_h
        display_image = original_image

    # C. 重要修正：畫布背景強制轉為 RGB (解決 PNG 變白屏的關鍵！)
    canvas_bg = display_image.convert("RGB")

    # --- 3. 介面佈局 ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. 拉框操作區")
        mode = st.radio("選擇功能：", ("🟥 紅框 (挖掉)", "🟩 綠框 (救回)"), horizontal=True)
        
        # 設定畫筆顏色
        if mode == "🟥 紅框 (挖掉)":
            stroke = "#ff0000"
            fill = "rgba(255, 0, 0, 0.3)"
        else:
            stroke = "#00ff00"
            fill = "rgba(0, 255, 0, 0.3)"

        # 建立畫布
        canvas_result = st_canvas(
            fill_color=fill,
            stroke_width=2,
            stroke_color=stroke,
            background_image=canvas_bg, # 這裡傳入 RGB 縮圖，保證顯示
            update_streamlit=True,
            height=display_height,
            width=display_width,
            drawing_mode="rect", # 鎖定矩形模式 (最穩定)
            key="canvas_reset",
        )

    with col2:
        st.subheader("2. 預覽結果")

        # --- 4. 核心運算 (座標還原法) ---
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            
            if len(objects) > 0:
                # 轉成陣列準備開刀
                img_array = np.array(original_image)

                for obj in objects:
                    # 取得縮圖上的座標
                    small_left = obj["left"]
                    small_top = obj["top"]
                    small_w = obj["width"]
                    small_h = obj["height"]
                    color = obj["stroke"]

                    # 數學還原：把座標放大回原始尺寸
                    real_left = int(small_left * scale_factor)
                    real_top = int(small_top * scale_factor)
                    real_w = int(small_w * scale_factor)
                    real_h = int(small_h * scale_factor)

                    # 確保座標有效
                    if real_w > 0 and real_h > 0:
                        # 紅框 = 透明 (0)
                        if color == "#ff0000":
                            img_array[real_top : real_top+real_h, real_left : real_left+real_w, 3] = 0
                        # 綠框 = 實心 (255)
                        elif color == "#00ff00":
                            img_array[real_top : real_top+real_h, real_left : real_left+real_w, 3] = 255
                
                # 顯示結果
                final_image = Image.fromarray(img_array)
                st.image(final_image, caption=f"最終尺寸: {orig_w}x{orig_h}", use_column_width=True)

                # 下載按鈕
                buf = BytesIO()
                final_image.save(buf, format="PNG")
                byte_im = buf.getvalue()
                st.download_button("📥 下載成品 PNG", byte_im, "final.png", "image/png")
            else:
                st.info("👈 請在左邊拉框框")
