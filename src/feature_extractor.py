import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from utils import tokenize_vietnamese_text
from config import NGRAM_RANGE, MIN_DF, PROCESSED_KEYWORDS_PATH

def extract_and_aggregate_keywords(df_articles, text_column='text_for_keywords', 
                                   date_column='date_only', 
                                   save_to_csv=True, # Mặc định là True để giữ hành vi cũ nếu gọi riêng
                                   output_csv_path=None): 
    """
    Trích xuất N-grams, tổng hợp tần suất.
    save_to_csv: True nếu muốn lưu kết quả vào file CSV.
    output_csv_path: Đường dẫn tùy chọn để lưu CSV. Nếu None và save_to_csv=True, dùng PROCESSED_KEYWORDS_PATH.
    """
    if df_articles.empty or text_column not in df_articles.columns or date_column not in df_articles.columns:
        print("Error: DataFrame is empty or missing required columns for keyword extraction.")
        return pd.DataFrame()

    vectorizer = CountVectorizer(
        tokenizer=tokenize_vietnamese_text,
        ngram_range=NGRAM_RANGE,
        min_df=MIN_DF,
        stop_words=None 
    )

    corpus = df_articles[text_column].tolist()
    if not corpus:
        print("Error: Corpus is empty after selecting text column.")
        return pd.DataFrame()
    
    try:
        X = vectorizer.fit_transform(corpus)
        feature_names = vectorizer.get_feature_names_out()
    except ValueError as e:
        print(f"Error during CountVectorizer fit_transform: {e}")
        return pd.DataFrame()

    if X.shape[0] == 0 or X.shape[1] == 0:
        print("No features extracted. Vocabulary might be empty.")
        return pd.DataFrame()

    keywords_in_docs_list = []
    dates = df_articles[date_column].tolist()

    for i in range(X.shape[0]):
        doc_vector = X[i]
        doc_date = dates[i]
        for col_idx in doc_vector.nonzero()[1]:
            keyword = feature_names[col_idx]
            frequency = doc_vector[0, col_idx]
            keywords_in_docs_list.append({
                'date': doc_date,
                'keyword': keyword,
                'frequency_in_doc': int(frequency)
            })
    
    if not keywords_in_docs_list:
        print("No keywords found in any documents.")
        return pd.DataFrame()

    df_keywords_in_docs = pd.DataFrame(keywords_in_docs_list)
    daily_keyword_frequency = df_keywords_in_docs.groupby(['date', 'keyword'])['frequency_in_doc'].sum().reset_index()
    daily_keyword_frequency.rename(columns={'frequency_in_doc': 'daily_total_frequency'}, inplace=True)
    
    if not daily_keyword_frequency.empty:
        print(f"Extracted {len(daily_keyword_frequency['keyword'].unique())} unique keywords across {len(df_articles)} documents for this run.")
    
    # --- Logic lưu file được cập nhật ---
    if save_to_csv:
        # Ưu tiên output_csv_path nếu được cung cấp, ngược lại dùng PROCESSED_KEYWORDS_PATH
        path_to_save = output_csv_path if output_csv_path else PROCESSED_KEYWORDS_PATH
        
        try:
            # Đảm bảo thư mục cha của path_to_save tồn tại
            save_directory = os.path.dirname(path_to_save)
            if save_directory and not os.path.exists(save_directory): # Kiểm tra save_directory có rỗng không
                os.makedirs(save_directory)
                print(f"Created directory for CSV: {save_directory}")
            
            daily_keyword_frequency.to_csv(path_to_save, index=False, encoding='utf-8-sig')
            print(f"Processed daily keyword frequencies saved to {path_to_save}")
        except Exception as e:
            print(f"Error saving processed keywords to CSV at {path_to_save}: {e}")

    return daily_keyword_frequency

# Phần if __name__ == '__main__': để test có thể giữ nguyên hoặc sửa lại cách gọi hàm
if __name__ == '__main__':
    from src.data_loader import load_and_preprocess_data # Giả sử chạy từ thư mục gốc
    # from src.config import OUTPUT_DIR # Nếu bạn muốn lưu vào output từ config
    
    # Tạo thư mục output_test nếu chưa có để test
    test_output_dir = "output_test_feature_extractor" 
    if not os.path.exists(test_output_dir):
        os.makedirs(test_output_dir)

    sample_data = load_and_preprocess_data()
    if not sample_data.empty:
        print(f"\nProcessing {len(sample_data)} articles for keyword extraction (test run)...")
        
        # Test 1: Lưu vào đường dẫn mặc định từ config (PROCESSED_KEYWORDS_PATH)
        # extracted_kws_default = extract_and_aggregate_keywords(sample_data, save_to_csv=True)

        # Test 2: Lưu vào đường dẫn tùy chỉnh
        custom_path = os.path.join(test_output_dir, "custom_daily_keywords.csv")
        extracted_kws_custom = extract_and_aggregate_keywords(sample_data, save_to_csv=True, output_csv_path=custom_path)
        
        # Test 3: Không lưu file
        # extracted_kws_no_save = extract_and_aggregate_keywords(sample_data, save_to_csv=False)

        if not extracted_kws_custom.empty: # Hoặc dùng extracted_kws_default
            print("\nSample of daily keyword frequencies (from custom path save):")
            print(extracted_kws_custom.sort_values(by='daily_total_frequency', ascending=False).head(10))
        else:
            print("No keywords were extracted from the sample data.")
    else:
        print("Could not load data for feature extraction testing.")