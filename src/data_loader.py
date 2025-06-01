import pandas as pd
from config import DATA_FILE_PATH, URL_COLUMN, TITLE_COLUMN, CONTENT_COLUMN, DATE_COLUMN
from utils import parse_date_flexible, clean_text

def load_and_preprocess_data():
    """Tải dữ liệu từ CSV và tiền xử lý cơ bản."""
    try:
        # Specify UTF-8 encoding, common for Vietnamese text
        df = pd.read_csv(DATA_FILE_PATH, encoding='utf-8')
    except FileNotFoundError:
        print(f"Error: Data file not found at {DATA_FILE_PATH}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return pd.DataFrame()

    required_columns = [URL_COLUMN, TITLE_COLUMN, CONTENT_COLUMN, DATE_COLUMN]
    if not all(col in df.columns for col in required_columns):
        missing_cols = [col for col in required_columns if col not in df.columns]
        print(f"Error: CSV file must contain columns: {', '.join(required_columns)}. Missing: {', '.join(missing_cols)}")
        return pd.DataFrame()

    df[DATE_COLUMN] = df[DATE_COLUMN].apply(parse_date_flexible)
    df.dropna(subset=[DATE_COLUMN], inplace=True)
    df['date_only'] = df[DATE_COLUMN].dt.strftime('%Y-%m-%d')

    # Xử lý NaN trong text columns trước khi nối
    df[TITLE_COLUMN] = df[TITLE_COLUMN].fillna('')
    df[CONTENT_COLUMN] = df[CONTENT_COLUMN].fillna('')
    
    df['text_for_keywords'] = df[TITLE_COLUMN] + " " + df[CONTENT_COLUMN]
    df['text_for_keywords'] = df['text_for_keywords'].apply(clean_text)

    # Loại bỏ các hàng mà text_for_keywords rỗng sau khi làm sạch
    df = df[df['text_for_keywords'].str.strip() != '']

    print(f"Loaded and preprocessed {len(df)} articles.")
    if not df.empty:
        print(f"Date range in data: {df['date_only'].min()} to {df['date_only'].max()}")
    else:
        print("No articles remaining after preprocessing.")
    return df

if __name__ == '__main__':
    data = load_and_preprocess_data()
    if not data.empty:
        print("\nSample preprocessed data:")
        print(data[[DATE_COLUMN, 'date_only', 'text_for_keywords']].head())
    else:
        print("No data loaded or processed.")