import speech_recognition as sr

def record_and_recognize():
    """
    Sử dụng mic của máy tính để ghi âm và Google STT để lấy văn bản.
    Nhận diện bằng Tiếng Việt ('vi-VN').
    """
    r = sr.Recognizer()
    
    # Thiết lập cấu hình mic (chỉnh tuỳ môi trường chạy)
    with sr.Microphone() as source:
        print("Đang điều chỉnh nhiễu nền...")
        r.adjust_for_ambient_noise(source, duration=1)
        
        print("Bắt đầu nghe...")
        try:
            # Lắng nghe âm thanh từ mic. Timeout sau 5 giây nếu không ai nói. 
            # Dừng ghi âm khi kết thúc câu (phrase_time_limit)
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            print("Đã nghe xong. Đang xử lý...")
            
            # Chú ý: dùng recognizer_google cần có Internet
            text = r.recognize_google(audio, language="vi-VN")
            return text
            
        except sr.WaitTimeoutError:
            print("Không nghe thấy gì (Timeout).")
            return "[Lỗi: Hết thời gian ghi âm vì không nghe thấy gì rấy]"
        except sr.UnknownValueError:
            print("Google Speech Recognition không thể nhận diện được audio")
            return "[Lỗi: Xin lỗi, tôi không nghe rõ câu đó.]"
        except sr.RequestError as e:
            print(f"Không thể gọi dịch vụ Google Speech Recognition; {e}")
            return f"[Lỗi mạng: Không thể kết nối API Google]"
        except Exception as e:
            print(f"Lỗi: {e}")
            return f"[Lỗi hệ thống: {e}]"
