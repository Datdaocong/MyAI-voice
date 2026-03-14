import re

# Từ khóa mục tiêu
KEYWORDS = ["tuyển sinh", "xét tuyển", "ptit", "aiot"]
DEFAULT_RESPONSE = "Vui lòng truy cập link bên dưới"
UDU_LINK = "https://tuyensinh.ptit.edu.vn/" # Sử dụng link tuyển sinh thật của PTIT

def check_keywords_and_respond(user_text):
    """
    Check if the user's text contains any of the target keywords.
    Returns a tuple: (response_text, link_url)
    """
    if not user_text:
        return "Xin lỗi, tôi chưa nghe rõ câu hỏi của bạn.", None

    text_lower = user_text.lower()
    
    # Check if any keyword is in the text
    found_keyword = any(keyword in text_lower for keyword in KEYWORDS)
    
    if found_keyword:
        return DEFAULT_RESPONSE, UDU_LINK
    
    # Future QA API Integration Point
    return handle_qa_api(user_text)

def handle_qa_api(user_text):
    """
    Placeholder for future QA API. 
    Currently returns a generic response when keywords aren't found.
    """
    # TODO: Implement API call here
    return "Câu hỏi của bạn đã được ghi nhận. Để biết thông tin chi tiết về các ngành khác, vui lòng theo dõi thông báo mới nhất.", None

def analyze_sentiment(user_text):
    """
    Placeholder for future Sentiment Analysis.
    Returns: 'Positive', 'Negative', or 'Neutral'
    """
    # TODO: Implement HuggingFace sentiment pipeline or simple heuristic
    return "Neutral"
