import re
from datetime import datetime, timedelta
from underthesea import word_tokenize
# Import các biến cần thiết từ src.config
from config import VIETNAMESE_STOPWORDS, FONT_PATH_FOR_WORDCLOUD 
# OUTPUT_DIR không còn cần thiết ở đây nếu generate_wordcloud_from_scores nhận full path
import pandas as pd
import unicodedata
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os

def normalize_vietnamese_text(text):
    """Chuẩn hóa dấu tiếng Việt."""
    if not isinstance(text, str):
        return ""
    return unicodedata.normalize('NFC', text)

def clean_text(text):
    """Làm sạch văn bản: bỏ ký tự đặc biệt, số, chuyển về chữ thường."""
    if not isinstance(text, str):
        return ""
    text = normalize_vietnamese_text(text)
    text = text.lower()
    text = re.sub(r'http\S+|www.\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\S*@\S*\s?', '', text, flags=re.MULTILINE)
    text = re.sub(r'[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize_vietnamese_text(text):
    """Tách từ tiếng Việt và loại bỏ stopwords."""
    if not isinstance(text, str) or not text.strip():
        return []
    try:
        tokens = word_tokenize(text, format="text").split()
    except Exception:
        return []
    filtered_tokens = [
        token for token in tokens
        if token not in VIETNAMESE_STOPWORDS and len(token) > 1
    ]
    return filtered_tokens

def parse_date_flexible(date_str_input): # Đổi tên tham số đầu vào cho rõ ràng
    """Chuyển đổi chuỗi ngày tháng sang đối tượng datetime với nhiều định dạng."""
    if pd.isna(date_str_input) or not date_str_input:
        return None
    
    # Chuyển thành chuỗi và loại bỏ khoảng trắng thừa
    # Sử dụng một tên biến nhất quán cho chuỗi đang được xử lý
    current_date_str = str(date_str_input).strip()

    # Loại bỏ tiền tố '- ' nếu có
    if current_date_str.startswith('- '):
        current_date_str = current_date_str[2:] # Bỏ đi 2 ký tự đầu tiên '- '
    elif current_date_str.startswith('-'): # Xử lý thêm trường hợp chỉ có dấu '-'
        current_date_str = current_date_str[1:] # Bỏ đi 1 ký tự đầu tiên '-'

    date_formats = [
        '%d/%m/%Y %H:%M',       # "dd/mm/yyyy HH:MM"
        '%Y-%m-%d %H:%M:%S',   # "yyyy-mm-dd HH:MM:SS"
        '%d/%m/%Y',            # "dd/mm/yyyy"
        '%Y-%m-%d',            # "yyyy-mm-dd"
    ]

    for fmt in date_formats:
        try:
            # Sử dụng current_date_str đã được làm sạch
            return datetime.strptime(current_date_str, fmt)
        except (ValueError, TypeError):
            continue
    
    # In ra chuỗi gốc ban đầu và chuỗi đã xử lý nếu không parse được
    print(f"Warning: Could not parse date '{current_date_str}' (original: '{str(date_str_input).strip()}') with any known format. Skipping.")
    return None

def format_keyword_for_display(keyword_str):
    """Thay thế '_' bằng ' ' và viết hoa chữ cái đầu mỗi từ."""
    if not isinstance(keyword_str, str):
        return keyword_str # Trả về nguyên bản nếu không phải string
    
    # Thay _ bằng khoảng trắng
    formatted_str = keyword_str.replace("_", " ")
    
    # Xử lý cho từ đơn và cụm từ
    words = formatted_str.split(' ')
    capitalized_words = [word.capitalize() for word in words]
    return ' '.join(capitalized_words)

def generate_wordcloud_from_scores(keyword_scores_df_input, output_image_path, top_n=50):
    """
    Tạo và lưu ảnh Word Cloud từ DataFrame chứa keywords và điểm số của chúng.
    keyword_scores_df_input: DataFrame với cột 'keyword' và một cột điểm.
    filename: Tên file để lưu ảnh Word Cloud.
    top_n: Số lượng keywords hàng đầu (dựa trên điểm số) để đưa vào Word Cloud.
    """
    if keyword_scores_df_input.empty:
        print("Cannot generate word cloud: Input DataFrame is empty.")
        return

    keyword_scores_df = keyword_scores_df_input.copy() # Tạo bản sao

    score_column = None
    possible_score_columns = ['trend_score', 'predicted_score_for_target_date', 'base_trend_score', 'recent_frequency']
    for col in possible_score_columns:
        if col in keyword_scores_df.columns:
            score_column = col
            break
    
    if not score_column:
        print(f"Cannot generate word cloud: Could not find a suitable score column in {keyword_scores_df.columns}.")
        return

    keyword_scores_df.loc[:, score_column] = pd.to_numeric(keyword_scores_df[score_column], errors='coerce')
    keyword_scores_df.dropna(subset=[score_column], inplace=True)

    if keyword_scores_df.empty:
        print("Cannot generate word cloud: DataFrame is empty after handling NaNs in score column.")
        return

    top_keywords_df = keyword_scores_df.sort_values(by=score_column, ascending=False).head(top_n)

    if top_keywords_df.empty:
        print(f"Cannot generate word cloud: No keywords left after filtering for top {top_n}.")
        return

    min_score = top_keywords_df[score_column].min()
    max_score = top_keywords_df[score_column].max()

    # --- BẮT ĐẦU SỬA ĐỔI Ở ĐÂY ---
    scaled_frequencies = {} 

    if max_score == min_score:
        default_freq = 50 if min_score <= 0 else int(min_score) 
        for index, row in top_keywords_df.iterrows():
            original_keyword = row['keyword']
            # Format keyword trước khi thêm vào dictionary
            display_keyword = format_keyword_for_display(original_keyword)
            scaled_frequencies[display_keyword] = default_freq
    else:
        for index, row in top_keywords_df.iterrows():
            if row[score_column] > 0:
                original_keyword = row['keyword']
                # Format keyword trước khi thêm vào dictionary
                display_keyword = format_keyword_for_display(original_keyword)
                frequency = max(1, int(1 + (row[score_column] - min_score) * 99 / (max_score - min_score)))
                scaled_frequencies[display_keyword] = frequency
    # --- KẾT THÚC SỬA ĐỔI ---
    
    if not scaled_frequencies:
        print("Cannot generate word cloud: No frequencies generated (all scores might be zero or negative, or no keywords left).")
        return

    font_path_to_use = FONT_PATH_FOR_WORDCLOUD 

    if not os.path.exists(font_path_to_use):
        print(f"CRITICAL ERROR: Font file not found at '{font_path_to_use}'. WordCloud cannot be generated correctly.")
        # ... (các print thông báo lỗi font) ...
        return 
    else:
        print(f"Using font: {font_path_to_use}")
    
    try:
        wordcloud = WordCloud(
            width=1200,
            height=800,
            background_color='white',
            font_path=font_path_to_use,
            min_font_size=10,
            collocations=False 
        ).generate_from_frequencies(scaled_frequencies) # scaled_frequencies giờ chứa key đã được format

        image_output_directory = os.path.dirname(output_image_path)
        if not os.path.exists(image_output_directory):
            os.makedirs(image_output_directory)
            print(f"Created directory for wordcloud image: {image_output_directory}")
        
        plt.figure(figsize=(12, 8), dpi=100) 
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.tight_layout(pad=0) 
        plt.savefig(output_image_path) # <--- SỬ DỤNG output_image_path trực tiếp
        plt.close() 
        
        print(f"Word Cloud saved to {output_image_path}")

    except Exception as e:
        print(f"Error generating or saving Word Cloud: {e}")
        if font_path_to_use and ("cannot open resource" in str(e).lower() or "specified font path is incorrect" in str(e).lower()):
            print(f"The font at '{font_path_to_use}' could not be opened or is not a valid font file.")
        elif not font_path_to_use and "font" in str(e).lower():
            print("WordCloud likely failed due to missing font or default font not supporting characters.")