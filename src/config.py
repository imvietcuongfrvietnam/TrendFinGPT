import os
from dotenv import load_dotenv

# Xác định thư mục gốc của dự án
# Giả sử config.py nằm trong src/, thư mục gốc là thư mục cha của src/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
print(f"DEBUG [config.py]: PROJECT_ROOT is {PROJECT_ROOT}")

# Tải biến môi trường từ file .env trong thư mục gốc
dotenv_path = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(dotenv_path)

# Đường dẫn dữ liệu (sử dụng os.path.join để đảm bảo tương thích đa nền tảng)
DEFAULT_DATA_FILE_PATH = os.path.join(PROJECT_ROOT, "crawl_data", "data", "baodautu.csv")
print(f"DEBUG [config.py]: DEFAULT_DATA_FILE_PATH is {DEFAULT_DATA_FILE_PATH}")
DEFAULT_PROCESSED_KEYWORDS_PATH = os.path.join(PROJECT_ROOT, "output", "processed_daily_keywords.csv")
DEFAULT_PREDICTED_TRENDS_PATH = os.path.join(PROJECT_ROOT, "output", "predicted_trends.json")

DATA_FILE_PATH = os.getenv("DATA_FILE_PATH", DEFAULT_DATA_FILE_PATH)
print(f"DEBUG [config.py]: FINAL DATA_FILE_PATH is {DATA_FILE_PATH}") # Dòng debug
print(f"DEBUG [config.py]: Value from os.getenv('DATA_FILE_PATH') is: {os.getenv('DATA_FILE_PATH')}") 
PROCESSED_KEYWORDS_PATH = os.getenv("PROCESSED_KEYWORDS_PATH", DEFAULT_PROCESSED_KEYWORDS_PATH)
PREDICTED_TRENDS_PATH = os.getenv("PREDICTED_TRENDS_PATH", DEFAULT_PREDICTED_TRENDS_PATH)

# Tạo thư mục output nếu chưa tồn tại
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

DEFAULT_FONT_FILENAME = "NotoSans-Regular.ttf" 
FONT_PATH_FOR_WORDCLOUD = os.path.join(PROJECT_ROOT, "fonts", DEFAULT_FONT_FILENAME)

# Cột trong CSV
URL_COLUMN = "url"
TITLE_COLUMN = "title"
CONTENT_COLUMN = "content"
DATE_COLUMN = "date"
# AUTHOR_COLUMN = "author" # Không dùng trong logic này nhưng có thể hữu ích sau này
# SUMMARY_COLUMN = "summary"

# Tham số xử lý
NGRAM_RANGE = (1, 3)  # Trích xuất unigrams, bigrams, trigrams
MIN_DF = 2  # Bỏ qua các từ/cụm từ xuất hiện ít hơn MIN_DF lần trong toàn bộ corpus

# Tham số dự đoán trend
RECENT_DAYS_WINDOW = 7
GROWTH_COMPARISON_WINDOW = 7
MIN_RECENT_FREQUENCY_FOR_TREND = 3 # Keyword phải xuất hiện ít nhất bao nhiêu lần trong RECENT_DAYS_WINDOW
TOP_K_TRENDING_KEYWORDS = 20 # Số lượng keyword trend hàng đầu để dự đoán
PREDICTION_HORIZON_DAYS = 1 # Dự đoán cho bao nhiêu ngày tới

# Dữ liệu stopword tiếng Việt (CẦN BỔ SUNG VÀ TINH CHỈNH CHO PHÙ HỢP)
VIETNAMESE_STOPWORDS = [
    # === Nhóm từ nối, giới từ, đại từ, trạng từ (bạn đã có khá đủ) ===
    "và", "là", "của", "trong", "cho", "có", "được", "với", "khi", "từ", "đến", "này", "đó", "ấy",
    "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín", "mười", "các", "những", "nhiều", "ít",
    "rằng", "thì", "mà", "như", "tại", "bởi", "vì", "nên", "nếu", "cũng", "đã", "sẽ", "đang",
    "để", "không", "chưa", "chẳng", "chả",
    "ra", "vào", "lên", "xuống", "qua", "lại", "rồi", "tiếp", "nữa", "vẫn", "còn",
    "anh", "chị", "em", "ông", "bà", "cô", "chú", "bác", "cụ",
    "tôi", "bạn", "chúng ta", "chúng tôi", "chúng nó", "họ", "mình", "ai", "người",
    "rất", "quá", "nhất", "cực", "vô cùng", "khá", "hoàn toàn", "tương đối", "khá là",
    "luôn", "chỉ", "ngay", "hãy", "thường", "thường xuyên", "hay", "bao giờ", "kịp",

    # === Nhóm thời gian, số lượng (bạn đã có) ===
    "ngày", "tháng", "năm", "quý", "tuần", "giờ", "phút", "giây", "sáng", "trưa", "chiều", "tối", "đêm",
    "hôm nay", "hôm qua", "ngày mai", "cuối tuần", "đầu tuần", "đầu năm", "cuối năm",
    "lần", "số", "lượng", "phần trăm", "%", "đồng", "vnd", "usd", "tỷ", "triệu", "nghìn",

    # === Nhóm từ chung chung về hành động, trạng thái, khái niệm ===
    "theo", "sau", "trước", "trên", "dưới", "ngoài", "trong đó", "ngoài ra",
    "gì", "đâu", "nào", "sao", "bao", "kia", "đây",
    "khác", "nhau", "cùng", "hơn", "kém", "so với", "tương tự", "giống như",
    "lớn", "nhỏ", "mới", "cũ", "cao", "thấp", "tốt", "xấu", "đẹp", "quan trọng", "cần thiết",
    "biết", "nói", "làm", "đi", "đứng", "ngồi", "thấy", "cần", "muốn", "phải", "nên", "có thể",
    "thứ", "việc", "điều", "vấn đề", "cách", "giải pháp", "kế hoạch", "chương trình", "dự án",
    "thông tin", "dữ liệu", "báo cáo", "nghiên cứu", "phân tích", "đánh giá", "ý kiến",
    "thực hiện", "triển khai", "áp dụng", "phát triển", "xây dựng", "tổ chức", "quản lý",
    "quy định", "chính sách", "pháp luật", "quyết định", "thông tư", "nghị định",
    "hoạt động", "quá trình", "giai đoạn",
    "hệ thống", "cơ cấu", "mô hình",
    "mục tiêu", "nhiệm vụ", "kết quả", "hiệu quả", "ảnh hưởng", "tác động",
    "do", "tuy nhiên", "đồng thời", "cụ thể", "ví dụ", "chẳng hạn", "nhất là",
    "hiện nay", "hiện tại", "gần đây", "sắp tới", "trong tương lai",
    "vừa qua", "thời gian", "thời điểm", "thời kỳ",
    "nhằm", "tiếp tục", "đặc biệt", "chủ yếu", "cơ bản", "nói chung",
    "liên quan", "bao gồm", "đối với", "về việc", "thay đổi", "điều chỉnh", "bổ sung",

    # === Nhóm từ đặc thù ngành tài chính/chứng khoán nhưng quá chung chung ===
    "ubcknn", "ủy ban chứng khoán nhà nước", "bộ tài chính", "sở giao dịch chứng khoán", "hose", "hnx", "upcom",
    "vsdc", "trung tâm lưu ký chứng khoán",
    "ftse russell", "msci", "wb", "ngân hàng thế giới", "imf",
    "agcsifma", # Tên hiệp hội (nếu xuất hiện nhiều mà không phải trend)
    "tt-btc", "tt", # Thông tư (bạn đã có)
    "thị trường", # Rất chung chung, có thể bỏ nếu muốn tập trung vào "thị trường X"
    # "chứng khoán", # "thị trường chứng khoán" cụ thể hơn
    "công ty", "doanh nghiệp", "tập đoàn", "tổ chức", # Nên giữ lại tên công ty cụ thể (ví dụ "vinamilk")
    "cổ phiếu", "cổ phần", "cổ đông", "trái phiếu", "trái chủ", "chứng chỉ quỹ",
    "giao dịch", "mua", "bán", "khớp lệnh", "thanh khoản", "giá", "biến động",
    "tài khoản", "mở tài khoản", "lưu ký",
    "nâng hạng", "thị trường cận biên", "thị trường mới nổi", # "nâng hạng thị trường" có thể là trend, nhưng các thành phần riêng lẻ có thể là stopword
    "đầu tư", "nhà đầu tư", "danh mục đầu tư", "quỹ đầu tư", "công ty quản lý quỹ",
    "lãi suất", "tỷ giá", "lạm phát", "tăng trưởng", "kinh tế", "tài chính",
    "ngân hàng", "ngân hàng nhà nước", "ngân hàng trung ương",
    "báo cáo tài chính", "doanh thu", "lợi nhuận", "cổ tức", "eps", "p/e",
    "rủi ro", "cơ hội", "tiềm năng", "triển vọng",
    "vốn", "huy động vốn", "phát hành", "niêm yết", "ủy thác",
    "thuế", "phí", "minh bạch", "công bố thông tin",
    "cuộc họp", "hội thảo", "sự kiện", "thông báo", "khuyến nghị",
    "việt nam", "trong nước", "quốc tế", "nước ngoài", # Có thể là stopword nếu không mang ý nghĩa trend cụ thể

    # === Từ/cụm từ do tokenizer tạo ra (nếu dùng pyvi và giữ lại "_") ===
    # Nếu bạn dùng pyvi và nó tạo ra "cao_su", "nhà_nước", bạn có thể cần thêm:
    # "thị_trường", "chứng_khoán", "công_ty", "cổ_phiếu", "giao_dịch", "tài_khoản",
    # "nhà_đầu_tư", "bộ_tài_chính", "ủy_ban_chứng_khoán_nhà_nước",

    # === Các từ thường gặp khác trong văn bản báo chí ===
    "cho biết", "theo ông", "theo bà", "đại diện", "chuyên gia", "nhận định", "dự báo",
    "được biết", "ghi nhận", "xuất hiện", "diễn ra",
    "thứ hai", "thứ ba", "thứ tư", "thứ năm", "thứ sáu", "thứ bảy", "chủ nhật", # Các thứ trong tuần
    "xin", "cảm ơn", "kính mời", "trân trọng",
    "hình ảnh", "video", "minh họa",
    "đọc thêm", "xem thêm", "chi tiết", "tại đây",
    "đáng chú ý", "đáng kể", "đáng quan tâm",
    "nguồn", "tổng hợp", "lô", "nam"
    # ... tiếp tục thêm dựa trên việc xem xét output ...
]