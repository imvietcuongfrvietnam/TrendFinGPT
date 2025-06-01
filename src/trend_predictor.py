import pandas as pd
from datetime import datetime, timedelta
import json
from config import (
    RECENT_DAYS_WINDOW,
    GROWTH_COMPARISON_WINDOW,
    MIN_RECENT_FREQUENCY_FOR_TREND,
    TOP_K_TRENDING_KEYWORDS,
    PREDICTED_TRENDS_PATH,
    PREDICTION_HORIZON_DAYS
)

def calculate_trend_scores(df_daily_keywords, today_str=None):
    if df_daily_keywords.empty:
        print("Warning: No daily keyword data to calculate trends.")
        return pd.DataFrame()

    # Đảm bảo cột 'date' là datetime
    df_daily_keywords['date'] = pd.to_datetime(df_daily_keywords['date'])

    if today_str:
        today = pd.to_datetime(today_str)
    else:
        today = df_daily_keywords['date'].max()
        if pd.isna(today):
             print("Error: Could not determine 'today' from data. Max date is NaT.")
             return pd.DataFrame()
        print(f"No 'today_str' provided. Using max date from data as 'today': {today.strftime('%Y-%m-%d')}")

    all_keywords = df_daily_keywords['keyword'].unique()
    trend_data = []

    for keyword in all_keywords:
        kw_data_full = df_daily_keywords[df_daily_keywords['keyword'] == keyword].copy()
        
        # Tạo một chuỗi ngày đầy đủ từ min_date đến today cho keyword này
        # Điều này quan trọng để tính toán chính xác, kể cả những ngày keyword không xuất hiện
        min_date_kw = kw_data_full['date'].min()
        if pd.isna(min_date_kw): continue # Bỏ qua nếu keyword không có ngày hợp lệ

        # Chỉ tạo date_range nếu min_date_kw <= today
        if min_date_kw > today:
            date_range = pd.date_range(start=today, end=today, freq='D')
        else:
            date_range = pd.date_range(start=min_date_kw, end=today, freq='D')

        kw_data = pd.DataFrame({'date': date_range})
        kw_data = pd.merge(kw_data, kw_data_full[['date', 'daily_total_frequency']], on='date', how='left').fillna(0)

        # 1. Tần suất gần đây
        recent_start_date = today - timedelta(days=RECENT_DAYS_WINDOW - 1)
        recent_freq_df = kw_data[(kw_data['date'] >= recent_start_date) & (kw_data['date'] <= today)]
        recent_total_frequency = recent_freq_df['daily_total_frequency'].sum()

        if recent_total_frequency < MIN_RECENT_FREQUENCY_FOR_TREND:
            continue

        # 2. Tần suất trong cửa sổ so sánh trước đó
        previous_window_end_date = recent_start_date - timedelta(days=1)
        previous_window_start_date = previous_window_end_date - timedelta(days=GROWTH_COMPARISON_WINDOW - 1)
        
        previous_freq_df = kw_data[(kw_data['date'] >= previous_window_start_date) & (kw_data['date'] <= previous_window_end_date)]
        previous_total_frequency = previous_freq_df['daily_total_frequency'].sum()

        # 3. Tính Growth Rate và Trend Score
        growth_rate = 0
        if previous_total_frequency > 0:
            growth_rate = (recent_total_frequency - previous_total_frequency) / previous_total_frequency
        elif recent_total_frequency > 0: # previous=0, recent > 0
            growth_rate = 5 # Giá trị lớn tượng trưng cho sự bùng nổ (có thể điều chỉnh)
        
        # Trend score: ưu tiên tần suất cao và tăng trưởng dương
        # Nhân tố (1 + growth_rate) sẽ khuếch đại nếu growth_rate dương, giảm nếu âm
        # Có thể dùng max(0, growth_rate) nếu chỉ muốn thưởng cho tăng trưởng dương
        trend_score = recent_total_frequency * (1 + growth_rate * 0.5) # Giảm nhẹ ảnh hưởng của growth_rate

        trend_data.append({
            'keyword': keyword,
            'recent_frequency': int(recent_total_frequency),
            'previous_frequency': int(previous_total_frequency),
            'growth_rate': round(growth_rate, 2),
            'trend_score': round(trend_score, 2),
            'calculation_date': today.strftime('%Y-%m-%d')
        })

    if not trend_data:
        print("No keywords met the criteria for trend calculation.")
        return pd.DataFrame()

    df_trends = pd.DataFrame(trend_data)
    df_trends = df_trends.sort_values(by='trend_score', ascending=False).reset_index(drop=True)
    
    return df_trends

def predict_future_trends_from_scores(df_current_trends):
    if df_current_trends.empty:
        print("No current trend data to make predictions.")
        return []

    top_trending_keywords = df_current_trends.head(TOP_K_TRENDING_KEYWORDS)
    
    if top_trending_keywords.empty:
        print("No keywords in top current trends to predict.")
        return []

    calc_date_str = top_trending_keywords['calculation_date'].iloc[0]
    calc_date = datetime.strptime(calc_date_str, '%Y-%m-%d')
    
    all_predictions = []
    for i in range(1, PREDICTION_HORIZON_DAYS + 1):
        target_date = (calc_date + timedelta(days=i)).strftime('%Y-%m-%d')
        for rank, row in enumerate(top_trending_keywords.itertuples()):
            # Giả định đơn giản: score giảm dần theo thời gian dự đoán xa hơn
            # Ví dụ: giảm 2% giá trị mỗi ngày trong tương lai (có thể điều chỉnh)
            decay_factor = (1 - 0.02 * (i-1))
            predicted_score_for_day = row.trend_score * decay_factor
            
            all_predictions.append({
                "prediction_generated_date": calc_date_str,
                "target_forecast_date": target_date,
                "rank": rank + 1,
                "keyword": row.keyword,
                "base_trend_score": row.trend_score, # Điểm gốc tại ngày tính toán
                "predicted_score_for_target_date": round(max(0, predicted_score_for_day),2) # Đảm bảo không âm
            })
            
    try:
        with open(PREDICTED_TRENDS_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_predictions, f, ensure_ascii=False, indent=4)
        print(f"Predicted trends for next {PREDICTION_HORIZON_DAYS} days saved to {PREDICTED_TRENDS_PATH}")
    except Exception as e:
        print(f"Error saving predicted trends to JSON: {e}")
        
    return all_predictions

if __name__ == '__main__':
    # Tạo dữ liệu giả để test
    sample_dates = pd.to_datetime([
        '2023-01-01', '2023-01-01', '2023-01-02', '2023-01-03', '2023-01-03', 
        '2023-01-05', '2023-01-06', '2023-01-07', '2023-01-07', '2023-01-07', 
        '2023-01-08', '2023-01-08', '2023-01-09', '2023-01-10', '2023-01-10'
    ]).strftime('%Y-%m-%d')
    
    sample_keywords_data = {
        'date': sample_dates,
        'keyword': [
            'apple', 'banana', 'apple', 'apple', 'banana',
            'apple', 'apple', 'apple', 'banana', 'orange',
            'apple', 'grape', 'apple', 'apple', 'grape'
        ],
        'daily_total_frequency': [
            5, 3, 6, 10, 5, 
            12, 15, 20, 8, 4,
            22, 10, 25, 30, 12
        ]
    }
    df_sample_daily_keywords = pd.DataFrame(sample_keywords_data)
    print("Sample daily keywords for trend calculation:")
    print(df_sample_daily_keywords)

    test_today_str = '2023-01-10'
    print(f"\nCalculating trends as of {test_today_str}...")
    calculated_trends = calculate_trend_scores(df_sample_daily_keywords, today_str=test_today_str)

    if not calculated_trends.empty:
        print("\nCalculated Trend Scores:")
        print(calculated_trends.head(10))

        print(f"\nPredicting top trends for the next {PREDICTION_HORIZON_DAYS} days...")
        future_predictions = predict_future_trends_from_scores(calculated_trends)
        
        if future_predictions:
            print(f"\nSample of Future Predictions (first 5 of {len(future_predictions)}):")
            for pred_entry in future_predictions[:5]:
                print(pred_entry)
        else:
            print("No future predictions generated.")
    else:
        print("No trends were calculated from the sample data.")