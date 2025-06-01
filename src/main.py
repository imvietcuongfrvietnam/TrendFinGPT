# src/main.py
from datetime import datetime, timedelta, date
from data_loader import load_and_preprocess_data
from feature_extractor import extract_and_aggregate_keywords
from trend_predictor import calculate_trend_scores, predict_future_trends_from_scores
from config import (
    TOP_K_TRENDING_KEYWORDS, PREDICTION_HORIZON_DAYS, DATE_COLUMN, 
    OUTPUT_DIR, # OUTPUT_DIR cần ở đây để tạo current_output_dir
    # FONT_PATH_FOR_WORDCLOUD # Không cần ở main.py nữa, utils tự lấy từ config
)
# from utils import generate_wordcloud_from_scores
import pandas as pd
import os
import json

def run_pipeline_for_single_date(target_date_str, all_articles_df, days_of_data_to_consider=60, daily_output_subdir=""):
    """
    Chạy pipeline cho một ngày cụ thể, lưu output vào thư mục con nếu có.
    daily_output_subdir: Thư mục con để lưu output của ngày này (ví dụ: "2023-01-01")
    """
    print(f"\n--- Running Pipeline for Target Date: {target_date_str} ---")

    # Tạo thư mục output riêng cho ngày này nếu có subdir
    current_output_dir = OUTPUT_DIR
    if daily_output_subdir:
        current_output_dir = os.path.join(OUTPUT_DIR, daily_output_subdir)
        if not os.path.exists(current_output_dir):
            os.makedirs(current_output_dir)
            print(f"Created daily output directory: {current_output_dir}")

    # Xác định ngày "hôm nay" để tính toán
    today = datetime.strptime(target_date_str, '%Y-%m-%d')
    
    # Lọc dữ liệu trong khoảng thời gian xem xét (N ngày TRƯỚC target_date_str)
    # Ví dụ: nếu target_date_str là 2023-01-30 và days_of_data_to_consider=30
    # thì start_date_for_data sẽ là 2023-01-01
    start_date_for_data = today - timedelta(days=days_of_data_to_consider - 1)

    # Lấy dữ liệu từ all_articles_df cho đến 'today' (target_date_str)
    # và dữ liệu dùng để tính toán là từ start_date_for_data đến 'today'
    df_articles_up_to_today = all_articles_df[all_articles_df[DATE_COLUMN] <= today].copy()
    df_articles_filtered_for_calculation = df_articles_up_to_today[df_articles_up_to_today[DATE_COLUMN] >= start_date_for_data].copy()

    if df_articles_filtered_for_calculation.empty:
        print(f"Pipeline for {target_date_str} skipped: No data found within the last {days_of_data_to_consider} days from {target_date_str}.")
        return
    print(f"Using {len(df_articles_filtered_for_calculation)} articles from {start_date_for_data.strftime('%Y-%m-%d')} to {target_date_str} for calculations.")

    # 2. Trích xuất keywords và tính tần suất hàng ngày (chỉ trên dữ liệu được lọc)
    print(f"\n[Step 2/4 for {target_date_str}] Extracting keywords...")
    df_daily_keywords = extract_and_aggregate_keywords(
        df_articles_filtered_for_calculation,
        save_to_csv=False  # <--- Quan trọng: Đặt là False
    )
    if df_daily_keywords.empty:
        print(f"Pipeline for {target_date_str} skipped: No keywords extracted.")
        return

    # 3. Tính điểm trend hiện tại (dựa trên target_date_str)
    print(f"\n[Step 3/4 for {target_date_str}] Calculating current trend scores...")
    df_current_trends = calculate_trend_scores(df_daily_keywords, today_str=target_date_str)
    if df_current_trends.empty:
        print(f"Pipeline for {target_date_str} skipped: No current trends calculated.")
        return
    
    print(f"\nTop {min(10, len(df_current_trends))} current trends (as of {target_date_str}):")
    print(df_current_trends.head(min(10, len(df_current_trends))))

    # Lưu df_current_trends cho ngày này
    current_trends_filename = f"current_trends_{target_date_str.replace('-', '')}.csv"
    df_current_trends.to_csv(os.path.join(current_output_dir, current_trends_filename), index=False, encoding='utf-8-sig')
    print(f"Current trends for {target_date_str} saved to {os.path.join(current_output_dir, current_trends_filename)}")


    # Tạo Word Cloud cho current trends
    # if not df_current_trends.empty:
    #     print(f"\nGenerating Word Cloud for current trends as of {target_date_str}...")
    #     wc_filename_current = f"current_trends_wordcloud_{target_date_str.replace('-', '')}.png"
        
    #     # Truyền output_dir đã được cập nhật vào hàm generate_wordcloud
    #     # Hàm generate_wordcloud_from_scores cần được sửa để nhận output_dir
    #     # Hoặc chúng ta sửa hàm generate_wordcloud_from_scores để nó dùng OUTPUT_DIR từ config,
    #     # và chúng ta sẽ cần thay đổi OUTPUT_DIR tạm thời hoặc truyền đường dẫn đầy đủ.
    #     # Cách đơn giản là sửa generate_wordcloud_from_scores để nhận full path.
    #     # Hiện tại hàm utils.generate_wordcloud_from_scores dùng OUTPUT_DIR từ config và filename
    #     # Chúng ta sẽ tạo filename có chứa subdir
    #     full_wc_save_path = os.path.join(current_output_dir, wc_filename_current)
        
    #     # Để utils.generate_wordcloud_from_scores hoạt động đúng với current_output_dir,
    #     # một cách là truyền trực tiếp đường dẫn đầy đủ cho việc lưu file,
    #     # hoặc sửa hàm đó để nhận output_directory.
    #     # Giả sử sửa utils.generate_wordcloud_from_scores để nhận output_path đầy đủ
    #     # (Xem sửa đổi ở dưới)
    #     generate_wordcloud_from_scores(
    #         df_current_trends, 
    #         output_image_path=full_wc_save_path, # Truyền đường dẫn đầy đủ
    #         top_n=50
    #     )

    # 4. Dự đoán trend cho N ngày tới (từ target_date_str)
    print(f"\n[Step 4/4 for {target_date_str}] Predicting future trends...")
    predictions = predict_future_trends_from_scores(df_current_trends)
    
    if predictions:
        print(f"\nSuccessfully generated {len(predictions)} prediction entries starting from {target_date_str}.")
        
        # Lưu file JSON dự đoán cho ngày này
        predictions_filename = f"predicted_trends_{target_date_str.replace('-', '')}.json"
        with open(os.path.join(current_output_dir, predictions_filename), 'w', encoding='utf-8') as f:
            json.dump(predictions, f, ensure_ascii=False, indent=4)
        print(f"Predictions from {target_date_str} saved to {os.path.join(current_output_dir, predictions_filename)}")

        # Tạo Word Cloud cho ngày dự đoán đầu tiên (ngày mai của target_date_str)
        # df_predictions = pd.DataFrame(predictions)
        # if not df_predictions.empty:
        #     tomorrow_target_date = (datetime.strptime(target_date_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        #     df_tomorrow_predictions = df_predictions[df_predictions['target_forecast_date'] == tomorrow_target_date]
            
        #     if not df_tomorrow_predictions.empty:
        #         print(f"\nGenerating Word Cloud for predicted trends for {tomorrow_target_date}...")
        #         wc_filename_predicted = f"predicted_trends_wordcloud_{tomorrow_target_date.replace('-', '')}.png"
        #         full_wc_predicted_save_path = os.path.join(current_output_dir, wc_filename_predicted)
        #         generate_wordcloud_from_scores(
        #             df_tomorrow_predictions,
        #             output_image_path=full_wc_predicted_save_path, # Truyền đường dẫn đầy đủ
        #             top_n=30
        #         )
    else:
        print(f"No future trend predictions were generated from {target_date_str}.")
        
    print(f"--- Pipeline for Target Date: {target_date_str} Finished ---")


if __name__ == '__main__':
    # 1. Tải toàn bộ dữ liệu một lần
    print("--- Main Process Started: Loading all data initially ---")
    df_all_articles_master = load_and_preprocess_data()

    if df_all_articles_master.empty:
        print("Main Process Stopped: No data loaded initially.")
    else:
        print(f"Master data loaded: {len(df_all_articles_master)} articles.")
        min_date_str = df_all_articles_master[DATE_COLUMN].min().strftime('%Y-%m-%d') if not df_all_articles_master.empty and pd.notna(df_all_articles_master[DATE_COLUMN].min()) else "N/A"
        max_date_str = df_all_articles_master[DATE_COLUMN].max().strftime('%Y-%m-%d') if not df_all_articles_master.empty and pd.notna(df_all_articles_master[DATE_COLUMN].max()) else "N/A"
        print(f"Master data date range: {min_date_str} to {max_date_str}")

        # --- ĐỊNH NGHĨA NGÀY KẾT THÚC MONG MUỐN ---
        # Ví dụ: ngày 11/03/2025
        try:
            # Đảm bảo end_loop_date_target là một đối tượng datetime
            end_loop_date_target_dt = datetime.strptime("2025-05-27", "%Y-%m-%d") 
            # Hoặc "2025-03-12" tùy bạn muốn ngày nào là ngày cuối cùng để *tính toán* trend
        except ValueError:
            print("Error: Invalid target end date string. Exiting.")
            exit()
            
        # Kiểm tra xem ngày kết thúc mong muốn có nằm trong khoảng dữ liệu của bạn không
        max_data_date = df_all_articles_master[DATE_COLUMN].max()
        if pd.isna(max_data_date):
             print("Error: Max date in data is invalid. Exiting.")
             exit()

        if end_loop_date_target_dt > max_data_date:
            print(f"Warning: Target end date {end_loop_date_target_dt.strftime('%Y-%m-%d')} is after the latest data date {max_data_date.strftime('%Y-%m-%d')}.")
            print(f"Using latest data date as the end date for the loop: {max_data_date.strftime('%Y-%m-%d')}")
            end_loop_date_dt = max_data_date
        
        # --- ĐỊNH NGHĨA NGÀY BẮT ĐẦU MONG MUỐN (2 tháng trước ngày kết thúc) ---
        # Giả sử "2 tháng" là khoảng 60 ngày
        # Hoặc bạn có thể dùng relativedelta từ dateutil nếu muốn tính chính xác hơn (ví dụ: trừ 2 tháng)
        # from dateutil.relativedelta import relativedelta
        # start_loop_date_dt = end_loop_date_target_dt - relativedelta(months=2)
        days_in_target_period = 60 # 2 tháng ~ 60 ngày
        start_loop_date_dt = end_loop_date_target_dt - timedelta(days=days_in_target_period - 1) # -1 vì bao gồm cả ngày cuối

        # Đảm bảo ngày bắt đầu không sớm hơn ngày dữ liệu đầu tiên của bạn
        min_data_date = df_all_articles_master[DATE_COLUMN].min()
        if pd.isna(min_data_date):
            print("Error: Min date in data is invalid. Exiting.")
            exit()
            
        if start_loop_date_dt < min_data_date:
            print(f"Warning: Calculated start date {start_loop_date_dt.strftime('%Y-%m-%d')} is before the earliest data date {min_data_date.strftime('%Y-%m-%d')}.")
            print(f"Using earliest data date as the start date for the loop: {min_data_date.strftime('%Y-%m-%d')}")
            start_loop_date_dt = min_data_date

        # Chuyển thành đối tượng date để lặp
        start_loop_date = start_loop_date_dt.date()
        end_loop_date = end_loop_date_target_dt.date() # Sử dụng ngày mục tiêu đã điều chỉnh (nếu cần)

        if start_loop_date > end_loop_date:
            print(f"Error: Start date {start_loop_date.strftime('%Y-%m-%d')} is after end date {end_loop_date.strftime('%Y-%m-%d')}. Nothing to process.")
        else:
            print(f"\n--- Starting Daily Pipeline Loop from {start_loop_date.strftime('%Y-%m-%d')} to {end_loop_date.strftime('%Y-%m-%d')} ---")
            
            current_loop_date = start_loop_date
            days_to_consider_for_each_run = 60 # Số ngày dữ liệu lịch sử để tính trend cho mỗi ngày (có thể bằng days_in_target_period hoặc khác)

            while current_loop_date <= end_loop_date:
                target_date_str_loop = current_loop_date.strftime('%Y-%m-%d')
                daily_output_folder_name = target_date_str_loop 
                
                run_pipeline_for_single_date(
                    target_date_str_loop, 
                    df_all_articles_master, 
                    days_of_data_to_consider=days_to_consider_for_each_run,
                    daily_output_subdir=daily_output_folder_name
                )
                current_loop_date += timedelta(days=1)
            
            print("\n--- All Daily Pipeline Runs Finished ---")