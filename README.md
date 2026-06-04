<h1 align="center">
🌱 Hệ Thống Trợ Lý Nông Nghiệp AI Thông Minh (Smart Farm Assistant)
</h1>
<div align="center">
  <img src="https://img.shields.io/badge/Smart%20Farm-AI%20Agriculture-brightgreen?style=for-the-badge" alt="Smart Farm">
</div>
<br>
<div align="center">

[![AI POWERED](https://img.shields.io/badge/-AI%20POWERED%20(Groq)-28a745?style=for-the-badge)](https://groq.com/)
[![FLASK WEB](https://img.shields.io/badge/-FLASK%20WEB-dc3545?style=for-the-badge)](https://flask.palletsprojects.com/)

</div>

<hr>

<h2 align="center">✨ Mô tả dự án</h2>
<p align="justify">
  Đây là dự án <strong>HỆ THỐNG TRỢ LÝ NÔNG NGHIỆP AI THÔNG MINH</strong> sử dụng <strong>Arduino + ESP32</strong>, kết hợp với <strong>cảm biến độ ẩm đất, cảm biến nhiệt độ, API thời tiết</strong> và <strong>AI Groq (LLaMA 3.3 70B)</strong>. Hệ thống tự động <strong>phân tích dữ liệu môi trường → quyết định tưới nước cây trồng</strong>, đồng thời có chức năng <strong>cảnh báo email</strong> khi độ ẩm bất thường và <strong>chatbot AI trợ lý nông nghiệp</strong>.
</p>

<hr>

<h2 align="center">🚀 Cấu trúc dự án</h2>
<pre>
NNTM/
├── 📄 app.py                       # Backend Flask chính - API & xử lý AI
├── 📁 templates/
│   └── 📄 index.html               # Dashboard web thời gian thực
├── 📁 static/
│   └── 📄 favicon.ico              # Icon trang web
├── 📊 data.json                    # Lịch sử tưới nước
├── 📊 alert_history.json           # Lịch sử cảnh báo
├── 📊 alert_status.json            # Trạng thái cảnh báo (legacy)
├── 🔐 nntm-firebase-adminsdk-*.json # Firebase credentials
└── 📘 README.md                    # Tài liệu dự án
</pre>

<hr>

<h2 align="center">✨ Tính Năng Chính</h2>

- 🤖 **AI Tự Động**: Phân tích độ ẩm đất, thời tiết, chỉ số NPK → quyết định tưới nước tối ưu
- 📊 **Dashboard Thời Gian Thực**: Hiển thị dữ liệu cảm biến, thời tiết, lời khuyên AI
- 📈 **Thống Kê & Biểu Đồ**: Xem tổng lượng nước, số lần bơm theo ngày/tuần/tháng
- 🚨 **Cảnh Báo Email**: Gửi email khi độ ẩm < 30% (khô) hoặc > 75% (ẩm)
- 💾 **Lịch Sử Chi Tiết**: Lưu trữ 50 cảnh báo gần nhất
- 🎛️ **Điều Khiển Thủ Công**: Bật/Tắt/Tự Động máy bơm
- 💬 **Chatbot AI**: Trợ lý nông nghiệp trả lời câu hỏi về cảm biến, nước tưới, dinh dưỡng
- 🌱 **Đa Loại Cây**: Hỗ trợ 4 loại cây (Lúa, Rau muống, Xương rồng, Chung)
- ⚡ **Kết Nối WiFi**: ESP32 không cần USB, chỉ cần WiFi + power bank

<hr>

## Chuẩn bị 
### 🛠️ Phần cứng

<div align="center">

[![ESP32](https://img.shields.io/badge/-ESP32-239121?style=for-the-badge&logo=esp32&logoColor=white)](#)
[![Arduino Uno](https://img.shields.io/badge/-ARDUINO%20UNO-00979D?style=for-the-badge&logo=arduino&logoColor=white)](#)
[![WiFi](https://img.shields.io/badge/-WIFI%20CONNECTION-007396?style=for-the-badge)](#)
[![Cảm Biến Độ Ẩm Đất](https://img.shields.io/badge/Cảm%20biến%20độ%20ẩm-FF5733?style=for-the-badge)](#)
[![Cảm Biến Nhiệt Độ](https://img.shields.io/badge/DHT22%20Temperature-5C3EE8?style=for-the-badge)](#)
[![Máy Bơm Nước](https://img.shields.io/badge/Water%20Pump%2012V-28B463?style=for-the-badge)](#)
[![Relay 5V](https://img.shields.io/badge/Relay%205V-F39C12?style=for-the-badge)](#)
[![Power Bank](https://img.shields.io/badge/Power%20Bank-FF6347?style=for-the-badge)](#)

</div>

### 💻 Phần mềm

<div align="center">

[![Python](https://img.shields.io/badge/-Python%203.8-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Flask](https://img.shields.io/badge/-Flask%202.0-000000?style=for-the-badge&logo=flask&logoColor=white)](#)
[![Firebase](https://img.shields.io/badge/-Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](#)
[![Groq AI](https://img.shields.io/badge/-Groq%20AI-00D084?style=for-the-badge)](#)
[![HTML5](https://img.shields.io/badge/-HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](#)
[![CSS3](https://img.shields.io/badge/-CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](#)
[![JavaScript](https://img.shields.io/badge/-JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](#)
[![Arduino IDE](https://img.shields.io/badge/-Arduino%20IDE-00979D?style=for-the-badge&logo=arduino&logoColor=white)](#)

</div>

<hr>

<h2 align="center">🔌 Kết Nối Hardware</h2>

### **ESP32 → Web Server**
```
ESP32 (WiFi)
├── GPIO34 → Cảm Biến Độ Ẩm Đất (Analog A0)
├── GPIO21 → DHT22 Data Pin (Nhiệt độ + Độ ẩm khí)
├── GPIO5  → Relay Signal → Máy Bơm (12V)
└── GND, 3.3V → Cấp nguồn cảm biến
```

### **Arduino ↔ ESP32 (Serial Communication - Tùy chọn)**
```
Arduino Uno          ESP32
GND        ----→    GND
RX (pin 0) ---→     TX2 (GPIO17)
TX (pin 1) ---→     RX2 (GPIO16)
```

<div align="center">
<table>
  <tr>
    <th>Thiết bị</th>
    <th>Chân/Pin</th>
    <th>Giá trị</th>
    <th>Ghi chú</th>
  </tr>
  <tr>
    <td>Cảm Biến Độ Ẩm</td>
    <td>A0 (ESP32: GPIO34)</td>
    <td>0-4095 (Analog)</td>
    <td>Đọc độ ẩm đất 0-100%</td>
  </tr>
  <tr>
    <td>DHT22 (Nhiệt độ)</td>
    <td>GPIO21 (ESP32)</td>
    <td>Digital</td>
    <td>Đọc nhiệt độ & độ ẩm khí</td>
  </tr>
  <tr>
    <td>Relay (Máy Bơm)</td>
    <td>GPIO5 (ESP32)</td>
    <td>Digital (HIGH/LOW)</td>
    <td>Điều khiển bật/tắt máy bơm</td>
  </tr>
  <tr>
    <td>Power Bank</td>
    <td>5V USB</td>
    <td>2A+</td>
    <td>Cấp nguồn cho ESP32</td>
  </tr>
</table>
</div>

<hr>

<h2 align="center">📦 Cài Đặt & Chạy</h2>

### 1️⃣ **Chuẩn bị Python & Thư Viện**
```bash
# Cài đặt Python 3.8+
# Tải từ: https://www.python.org/downloads/

# Di chuyển đến thư mục dự án
cd c:\Users\Admin\Desktop\NNTM

# Cài đặt thư viện cần thiết
pip install flask requests groq firebase-admin python-dotenv
```

### 2️⃣ **Cấu Hình API Keys & Firebase**
Mở `app.py` và chỉnh sửa:
```python
# Dòng ~62-71
GROQ_API_KEY = "your_groq_api_key_here"
WEATHER_API_KEY = "your_openweather_api_key_here"
CITY = "Hanoi"

ALERT_EMAIL_SENDER = "your_email@gmail.com"
ALERT_EMAIL_PASSWORD = "your_gmail_app_password"
ALERT_EMAIL_RECEIVER = "recipient_email@gmail.com"

FIREBASE_KEY_PATH = "path/to/nntm-firebase-adminsdk-*.json"
FIREBASE_DATABASE_URL = "https://nntm-6426b-default-rtdb.asia-southeast1.firebasedatabase.app/"
```

### 3️⃣ **Nạp Code ESP32 (Arduino IDE)**
```cpp
#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "WiFi_Name";
const char* password = "WiFi_Password";
const char* serverIP = "192.168.1.100";  // IP máy chạy Flask

void setup() {
  Serial.begin(115200);
  pinMode(34, INPUT);  // Cảm biến độ ẩm
  WiFi.begin(ssid, password);
}

void loop() {
  int moisture = analogRead(34);
  int percent = map(moisture, 0, 4095, 0, 100);
  
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = "http://" + String(serverIP) + ":5000/update-sensor";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    String json = "{\"moisture\": " + String(percent) + "}";
    http.POST(json);
    http.end();
  }
  delay(3000);
}
```

### 4️⃣ **Chạy Flask Server**
```bash
python app.py
```

Mở trình duyệt: `http://localhost:5000`

<hr>

<h2 align="center">🎯 Quy Trình Hoạt Động</h2>

<div align="center">
  <img src="https://img.shields.io/badge/Step%201-Đọc%20Cảm%20Biến-blue?style=for-the-badge" alt="Step 1">
  <br>
  ESP32 đọc độ ẩm, nhiệt độ từ cảm biến
  <br><br>
  
  <img src="https://img.shields.io/badge/Step%202-Gửi%20Dữ%20Liệu-green?style=for-the-badge" alt="Step 2">
  <br>
  Gửi JSON qua WiFi tới Flask Server
  <br><br>
  
  <img src="https://img.shields.io/badge/Step%203-AI%20Phân%20Tích-orange?style=for-the-badge" alt="Step 3">
  <br>
  Groq AI phân tích → quyết định tưới nước
  <br><br>
  
  <img src="https://img.shields.io/badge/Step%204-Điều%20Khiển-red?style=for-the-badge" alt="Step 4">
  <br>
  Bật/Tắt máy bơm tự động
  <br><br>
  
  <img src="https://img.shields.io/badge/Step%205-Dashboard-purple?style=for-the-badge" alt="Step 5">
  <br>
  Web dashboard cập nhật thời gian thực ✅
</div>

<hr>

<h2 align="center">📊 Cấu Hình Cây Trồng</h2>

<div align="center">
<table>
  <tr>
    <th>Loại Cây</th>
    <th>Ngưỡng Ẩm Tối Thiểu (%)</th>
    <th>Ngưỡng Ẩm Tối Đa (%)</th>
    <th>Ghi Chú</th>
  </tr>
  <tr>
    <td>Lúa Nước</td>
    <td>70</td>
    <td>90</td>
    <td>Yêu cầu ẩm cao</td>
  </tr>
  <tr>
    <td>Rau Muống</td>
    <td>60</td>
    <td>80</td>
    <td>Ẩm vừa phải</td>
  </tr>
  <tr>
    <td>Xương Rồng</td>
    <td>10</td>
    <td>25</td>
    <td>Khô ráo, ít nước</td>
  </tr>
  <tr>
    <td>Cây Chung (Mặc định)</td>
    <td>30</td>
    <td>75</td>
    <td>Cây trồng thông thường</td>
  </tr>
</table>
</div>

<hr>

<h2 align="center">🌐 API Endpoints</h2>

<div align="center">
<table>
  <tr>
    <th>Endpoint</th>
    <th>Method</th>
    <th>Chức Năng</th>
  </tr>
  <tr>
    <td>/</td>
    <td>GET</td>
    <td>Trang chủ dashboard</td>
  </tr>
  <tr>
    <td>/get-data</td>
    <td>GET</td>
    <td>Dữ liệu thời gian thực (độ ẩm, thời tiết, lời khuyên AI)</td>
  </tr>
  <tr>
    <td>/update-sensor</td>
    <td>POST</td>
    <td>Cập nhật độ ẩm từ ESP32</td>
  </tr>
  <tr>
    <td>/control-pump</td>
    <td>POST</td>
    <td>BẬT/TẮT/TỰ ĐỘNG máy bơm</td>
  </tr>
  <tr>
    <td>/update-npk</td>
    <td>POST</td>
    <td>Cập nhật chỉ số NPK</td>
  </tr>
  <tr>
    <td>/set-crop</td>
    <td>POST</td>
    <td>Chọn loại cây</td>
  </tr>
  <tr>
    <td>/get-statistics</td>
    <td>GET</td>
    <td>Thống kê theo ngày/tuần/tháng</td>
  </tr>
  <tr>
    <td>/get-alert-history</td>
    <td>GET</td>
    <td>Lịch sử cảnh báo</td>
  </tr>
  <tr>
    <td>/chat</td>
    <td>POST</td>
    <td>Chatbot AI trợ lý nông nghiệp</td>
  </tr>
</table>
</div>

<hr>

<h2 align="center">⚙️ Cách Sử Dụng Dashboard</h2>

### 📱 **Bảng Điều Khiển (Dashboard)**
- ✅ Xem độ ẩm đất, nhiệt độ, độ ẩm khí thời gian thực
- ✅ Xem dự báo thời tiết 3 giờ tới
- ✅ Xem lời khuyên từ AI Groq
- ✅ Xem trạng thái máy bơm (BẬT/TẮT/CẢNH BÁO)

### ⚙️ **Sidebar Menu**
- 🎛️ **Điều Khiển Bơm**: BẬT / TẮT / TỰ ĐỘNG (AI)
- 📊 **Nhập NPK**: Cập nhật chỉ số Nitơ, Phốt-pho, Kali
- 🌱 **Chọn Loại Cây**: Lúa, Rau muống, Xương rồng, Chung

### 📈 **Thống Kê & Biểu Đồ (Statistics)**
- 📅 Lọc theo: Hôm nay / Tuần này / Tháng này
- 📊 Xem: Tổng lượng nước, số lần bơm, lượng nước TB
- 📉 Biểu đồ: Cột xanh (lượng nước) + cột cam (số lần bơm)

### 🔔 **Cảnh Báo (Alerts)**
- 📝 Xem lịch sử cảnh báo gần đây (50 bản ghi)
- 🚨 Tự động gửi email khi:
  - ⚠️ Độ ẩm < 30% (khô) → bật máy bơm
  - ⚠️ Độ ẩm > 75% (ẩm) → tắt máy bơm

### 💬 **Chatbot AI**
- 🤖 Hỏi câu hỏi về trạng thái cảm biến
- 🌾 Hỏi về lịch tưới nước, dinh dưỡng NPK
- 📊 Nhận khuyến cáo từ AI Groq

<hr>

<h2 align="center">🧪 Các Tính Năng Bảo Vệ</h2>

### ⏱️ **Timeout Cảm Biến**
- Nếu không nhận dữ liệu > 30 giây → báo **"⚠️ CHƯA KẾT NỐI"**
- Tắt tất cả automations, không bơm nước tự động
- Chatbot sẽ thông báo lỗi kết nối

### 📧 **Email Cảnh Báo**
- Chỉ gửi khi cảm biến đã kết nối
- Ngừng gửi nếu cảm biến mất kết nối
- Ghi lại lịch sử 50 cảnh báo gần nhất

### 🧠 **Cache Dữ Liệu**
- Lưu trữ lịch sử tưới (10 bản ghi) trong `data.json`
- Lưu trữ lịch sử cảnh báo (50 bản ghi) trong `alert_history.json`
- Tự động sync lên Firebase Realtime Database

<hr>

<h2 align="center">🐛 Khắc Phục Sự Cố</h2>

| Vấn Đề | Giải Pháp |
|--------|----------|
| **ESP32 không kết nối WiFi** | Kiểm tra SSID/Password, khoảng cách từ router |
| **Dashboard không hiện dữ liệu** | Kiểm tra IP máy chạy Flask, firewall |
| **Email cảnh báo không gửi** | Bật "Less secure apps" hoặc dùng Gmail App Password |
| **AI không trả lời** | Kiểm tra Groq API key, hạn mức API |
| **Firebase không sync** | Kiểm tra file `serviceAccountKey.json` và URL |
| **Cảm biến chưa kết nối** | Kiểm tra kết nối dây, baud rate (115200) |

<hr>

<h2 align="center">📝 Giải Thích Code</h2>

### **app.py - Backend Flask**
```
1. get_groq_advice()     → Gọi AI Groq phân tích dữ liệu
2. /update-sensor        → Nhận dữ liệu từ ESP32
3. /get-data            → Trả về dashboard data
4. /control-pump        → BẬT/TẮT máy bơm
5. /chat                → Chatbot AI
```

### **templates/index.html - Frontend**
```
1. Dashboard Tab        → Hiển thị dữ liệu real-time
2. Statistics Tab       → Biểu đồ & thống kê
3. Alerts Tab          → Lịch sử cảnh báo
4. Floating Chatbot    → Hỏi đáp AI
```

<hr>

<h2 align="center">🤝 Tác Giả & Đóng Góp</h2>

<center>
<table>
  <thead>
    <tr>
      <th>Họ và Tên</th>
      <th>Vai Trò</th>
      <th>Mô Tả</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Ngô Tuấn Minh</td>
      <td>Developer</td>
      <td>Phát triển toàn bộ hệ thống Smart Farm AI</td>
    </tr>
  </tbody>
</table>
</center>

<hr>

<h2 align="center">📄 License</h2>

MIT License - Dự án mã nguồn mở

<hr>

<p align="center">
  © 2026 <strong>Hệ Thống Trợ Lý Nông Nghiệp AI (Smart Farm Assistant)</strong><br>
  <strong>Phiên bản:</strong> 2.3<br>
  <strong>Cập nhật:</strong> 04/06/2026
</p>
