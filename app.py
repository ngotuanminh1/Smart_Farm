from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
from datetime import datetime, timedelta
from groq import Groq
import time
import json
import os
import sys
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# --- FIREBASE SETUP ---

try:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DATABASE_URL
    })
    print("✅ Firebase initialized successfully!")
except Exception as e:
    print(f"⚠️ Firebase initialization warning: {e}")

# --- XỬ LÝ FAVICON ---
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# --- TẬP TIN LƯU TRỮ DỮ LIỆU ---
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

def load_data():
    """Đọc dữ liệu từ file JSON"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"pump_history": []}
    return {"pump_history": []}

def save_data(data):
    """Lưu dữ liệu vào file JSON"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Lưu dữ liệu thành công: {DATA_FILE}")
        
        # Sync lên Firebase
        sync_to_firebase(data)
    except Exception as e:
        print(f"❌ Lỗi lưu dữ liệu: {e}")

def sync_to_firebase(data):
    """Sync pump_history lên Firebase Realtime Database"""
    try:
        ref = db.reference('pump_history')
        # Lấy pump_history từ data.json
        pump_history = data.get('pump_history', [])
        # Giới hạn lưu 50 bản ghi gần nhất (để tiết kiệm)
        pump_history = pump_history[:50]
        # Lưu lên Firebase
        ref.set(pump_history)
        print(f"🔥 Sync Firebase thành công! ({len(pump_history)} records)")
    except Exception as e:
        print(f"❌ Lỗi sync Firebase: {e}")

# --- CẤU HÌNH API ---
GROQ_API_KEY = "" 
WEATHER_API_KEY = ""
CITY = "Hanoi"

# --- CẤU HÌNH EMAIL CẢNH BÁO ---
ALERT_EMAIL_SENDER = "wuveil215@gmail.com"
ALERT_EMAIL_PASSWORD = "kkeu aaum yikq zqlo"
ALERT_EMAIL_RECEIVER = "ngotuanminh2689@gmail.com"

client = Groq(api_key=GROQ_API_KEY)

# URLs cho thời tiết
CURRENT_URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=vi"
FORECAST_URL = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=vi"

CROP_DATABASE = {
    "mac_dinh": {"name": "Cây trồng chung", "min": 30, "max": 75},
    "lua": {"name": "Lúa nước", "min": 70, "max": 90},
    "rau_muong": {"name": "Rau muống", "min": 60, "max": 80},
    "xuong_rong": {"name": "Xương rồng", "min": 10, "max": 25}
}

# --- BIẾN TOÀN CỤC & CACHE ---
current_crop = "mac_dinh"
last_ai_time = 0
last_moisture_ai = -100
cached_advice = "Hệ thống đang khởi tạo..."

# Các biến phục vụ việc tính toán thời gian và lưu lượng nước bơm
last_pump_status = "OFF"
pump_start_time = None

# Biến tracking trạng thái cảnh báo (gửi mỗi khi thay đổi, không phải 1 lần/ngày)
is_currently_dry = False
is_currently_wet = False

# Biến tracking kết nối cảm biến
last_sensor_update_time = None  # Theo dõi lần cuối cảm biến gửi dữ liệu
sensor_connected = False  # Trạng thái kết nối cảm biến

# Load dữ liệu từ file JSON
persistent_data = load_data() 

sensor_data = {
    "moisture": None, "temp": 28, "weather_desc": "Mây cum", "humidity_air": 78,
    "wind_speed": 5, "rain": 0, "visibility": 10, "pressure": 1002,
    "next_temp": 30, "next_desc": "Trời nắng", "next_rain_prob": 10,
    "ai_advice": cached_advice,
    "pump_status": "OFF",  # KHÓA LỆNH CHUẨN CHO ESP32 ĐỌC: "ON" HOẶC "OFF"
    "pump_history": persistent_data.get("pump_history", []),    # Mảng lưu lịch sử tưới nước đổ ra giao diện web
    "timestamps": [], "moisture_history": [],
    "manual_mode": False,
    "pump_manual": "OFF",
    "n_val": 13, "p_val": 20, "k_val": 13,  # Dữ liệu NPK mặc định
    "sensor_connected": False  # Trạng thái kết nối cảm biến
}

def get_groq_advice(moisture, weather, crop_name):
    """Gọi Groq AI để phân tích đa chiều chuyên sâu và ép trả về mã điều khiển"""
    try:
        if moisture is None:
            return "Cảm biến chưa kết nối, không thể phân tích. [PUMP_OFF]"
            
        crop_info = CROP_DATABASE[current_crop]
        prompt = f"""
        Bối cảnh: Bạn là một Chuyên gia Nông nghiệp AI cao cấp.
        Dữ liệu thực tế từ trạm quan trắc:
        - Đối tượng: {crop_name} (Ngưỡng ẩm chuẩn: {crop_info['min']}% - {crop_info['max']}%)
        - Trạng thái đất: Độ ẩm hiện tại {moisture}%.
        - Chỉ số dinh dưỡng (NPK): N={sensor_data['n_val']}, P={sensor_data['p_val']}, K={sensor_data['k_val']} (mg/kg).
        - Thời tiết tại chỗ: {weather.get('desc', 'N/A')}, {weather.get('temp', '--')}°C, Gió {weather.get('wind', 0)}m/s.
        - Dự báo tương lai: {weather.get('next_desc', 'N/A')}, xác suất mưa {weather.get('next_rain_prob', 0)}%.

        Nhiệm vụ: 
        1. Phân tích sự phù hợp của độ ẩm với {crop_name}.
        2. Đánh giá nhanh tình trạng NPK (đủ hay thiếu hụt).
        3. Kết hợp dự báo thời tiết (nếu sắp mưa >60% thì ưu tiên dừng tưới để tiết kiệm).
        
        Yêu cầu phản hồi:
        - Văn phong: Chuyên nghiệp, thông minh, ngắn gọn (2-3 câu).
        - QUY TẮC BẮT BUỘC: Bạn phải kết thúc toàn bộ văn bản của mình bằng cụm cú pháp chính xác là [PUMP_ON] nếu quyết định bật bơm, hoặc [PUMP_OFF] nếu quyết định ngắt bơm. Không được gõ sai ký tự này.
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Bạn là bộ não của hệ thống Smart Farm, phân tích dữ liệu logic và đưa ra quyết định tưới tiêu."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            max_tokens=180, 
            temperature=0.2 
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Lỗi Groq API: {e}")
        return "Tắt máy bơm (Hệ thống AI đang bảo trì dữ liệu). [PUMP_OFF]"

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update-sensor', methods=['POST'])
def update_sensor():
    global last_sensor_update_time, sensor_connected
    try:
        data = request.json
        sensor_data["moisture"] = int(data.get('moisture', 0))
        last_sensor_update_time = time.time()  # Cập nhật lần cuối nhận dữ liệu
        sensor_connected = True  # Đánh dấu cảm biến đã kết nối
        sensor_data["sensor_connected"] = True
        
        now = datetime.now().strftime("%H:%M:%S")
        sensor_data["timestamps"].append(now)
        sensor_data["moisture_history"].append(sensor_data["moisture"])
        if len(sensor_data["timestamps"]) > 20:
            sensor_data["timestamps"].pop(0)
            sensor_data["moisture_history"].pop(0)
        return jsonify({"status": "success"})
    except:
        return jsonify({"status": "error"}), 500

@app.route('/update-npk', methods=['POST'])
def update_npk():
    global last_ai_time, last_moisture_ai
    data = request.json
    sensor_data["n_val"] = int(data.get('n', 0))
    sensor_data["p_val"] = int(data.get('p', 0))
    sensor_data["k_val"] = int(data.get('k', 0))
    last_ai_time = 0 
    last_moisture_ai = -100 # Ép xóa cache độ ẩm đất để AI tính toán lại ngay
    return jsonify({"status": "success"})

@app.route('/set-crop', methods=['POST'])
def set_crop():
    global current_crop, last_ai_time, last_moisture_ai
    current_crop = request.json.get('crop', 'mac_dinh')
    last_ai_time = 0
    last_moisture_ai = -100 # Ép xóa cache độ ẩm đất khi thay đổi cây trồng
    return jsonify({"status": "success"})

@app.route('/control-pump', methods=['POST'])
def control_pump():
    global sensor_data, last_pump_status, pump_start_time, persistent_data
    
    action = request.json.get('action')
    print(f"[DEBUG] /control-pump được gọi với action: {action}")
    
    if action == "ON":
        sensor_data["manual_mode"] = True
        sensor_data["pump_manual"] = "ON"
        sensor_data["pump_status"] = "ON"
        print(f"[DEBUG] Pump_status set to: ON")
        # Gọi ngay logic lưu dữ liệu
        save_pump_history("ON", True)
    elif action == "OFF":
        sensor_data["manual_mode"] = True
        sensor_data["pump_manual"] = "OFF"
        sensor_data["pump_status"] = "OFF"
        print(f"[DEBUG] Pump_status set to: OFF")
        # Gọi ngay logic lưu dữ liệu
        save_pump_history("OFF", True)
    else:
        sensor_data["manual_mode"] = False
        print(f"[DEBUG] Manual mode disabled")
    
    return jsonify({"status": "success"})

def save_alert_history(alert_type, moisture_value):
    """Lưu lịch sử cảnh báo vào file JSON"""
    try:
        alert_history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alert_history.json")
        
        # Đọc lịch sử cảnh báo hiện tại
        alert_history = []
        if os.path.exists(alert_history_file):
            with open(alert_history_file, 'r', encoding='utf-8') as f:
                alert_history = json.load(f)
        
        # Tạo entry mới
        new_alert = {
            "time": datetime.now().strftime("%H:%M:%S | %d/%m/%Y"),
            "type": alert_type,
            "moisture": moisture_value,
            "crop": CROP_DATABASE[current_crop]['name'],
            "message": f"Độ ẩm {'quá khô' if alert_type == 'DRY' else 'quá ẩm'}: {moisture_value}%"
        }
        
        # Thêm vào đầu danh sách và giới hạn 50 entry
        alert_history.insert(0, new_alert)
        if len(alert_history) > 50:
            alert_history = alert_history[:50]
        
        # Lưu vào file
        with open(alert_history_file, 'w', encoding='utf-8') as f:
            json.dump(alert_history, f, ensure_ascii=False, indent=2)
        
        print(f"📝 Lưu lịch sử cảnh báo {alert_type}: {new_alert}")
    except Exception as e:
        print(f"❌ Lỗi lưu lịch sử cảnh báo: {e}")

def send_alert_email(alert_type, moisture_value):
    """Gửi email cảnh báo khi độ ẩm bất thường"""
    try:
        # Chỉ gửi email khi cảm biến đã kết nối
        if not sensor_connected:
            print(f"⚠️ Cảm biến chưa kết nối, bỏ qua gửi email cảnh báo")
            return False
            
        if alert_type == "DRY":
            subject = f"🚨 CẢNH BÁO: Nông nghiệp thông minh"
            body = f"""Hệ thống Smart Farm phát hiện:

⚠️ DỮ LIỆU ĐẤT!

Thông tin chi tiết:
- Độ ẩm đất: {moisture_value}% (Ngưỡng: < 30%)
- Thời gian: {datetime.now().strftime("%H:%M:%S | %d/%m/%Y")}
- Cây trồng: {CROP_DATABASE[current_crop]['name']}

💧 HÀNH ĐỘNG: Vui lòng bật máy bơm ngay hoặc chuyển về chế độ tự động (AI)

---
Đây là tin nhắn tự động từ hệ thống Smart Farm"""
        
        elif alert_type == "WET":
            subject = f"🚨 CẢNH BÁO: Nông nghiệp thông minh"
            body = f"""Hệ thống Smart Farm phát hiện:

⚠️ DỮ LIỆU ĐẤT!

Thông tin chi tiết:
- Độ ẩm đất: {moisture_value}% (Ngưỡng: > 75%)
- Thời gian: {datetime.now().strftime("%H:%M:%S | %d/%m/%Y")}
- Cây trồng: {CROP_DATABASE[current_crop]['name']}

💨 HÀNH ĐỘNG: Vui lòng tắt máy bơm để tránh ngập nước

---
Đây là tin nhắn tự động từ hệ thống Smart Farm"""
        else:
            return False

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = ALERT_EMAIL_SENDER
        msg['To'] = ALERT_EMAIL_RECEIVER

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(ALERT_EMAIL_SENDER, ALERT_EMAIL_PASSWORD)
        server.sendmail(ALERT_EMAIL_SENDER, ALERT_EMAIL_RECEIVER, msg.as_string())
        server.quit()
        
        # Lưu lịch sử cảnh báo
        save_alert_history(alert_type, moisture_value)
        
        print(f"✉️ Gửi email cảnh báo ({alert_type}) thành công!")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi email cảnh báo: {e}")
        return False

def save_pump_history(status, is_manual):
    """Hàm lưu lịch sử bơm nước vào JSON"""
    global last_pump_status, pump_start_time, persistent_data
    
    # Chỉ lưu khi cảm biến đã kết nối
    if not sensor_connected and not is_manual:
        print(f"[DEBUG] Cảm biến chưa kết nối, bỏ qua lưu pump history tự động")
        return
    
    current_status = status
    print(f"[DEBUG] save_pump_history gọi - Status: {current_status}, Last: {last_pump_status}")
    
    if current_status != last_pump_status:
        try:
            now_str = datetime.now().strftime("%H:%M:%S | %d/%m/%Y")
            mode_text = "Thủ công" if is_manual else "Tự động (AI)"
            
            # Trường hợp 1: BẬT máy bơm
            if current_status == "ON" and last_pump_status == "OFF":
                pump_start_time = time.time()
                log_entry = {
                    "time": now_str,
                    "action": "Bắt đầu bật máy bơm",
                    "mode": mode_text,
                    "volume": "Đang tưới...",
                    "moisture": sensor_data["moisture"] if sensor_data["moisture"] is not None else "N/A",
                    "temp": sensor_data["temp"],
                    "humidity_air": sensor_data["humidity_air"],
                    "weather_desc": sensor_data["weather_desc"]
                }
                sensor_data["pump_history"].insert(0, log_entry)
                print(f"🟢 BẬT máy bơm - Moisture: {sensor_data['moisture']}%, Temp: {sensor_data['temp']}°C")

            # Trường hợp 2: TẮT máy bơm
            elif current_status == "OFF" and last_pump_status == "ON":
                volume_str = "0 ml"
                if pump_start_time is not None:
                    duration_seconds = round(time.time() - pump_start_time)
                    water_volume_ml = duration_seconds * 1
                    volume_str = f"{water_volume_ml} ml ({duration_seconds} giây)"
                    pump_start_time = None
                    
                log_entry = {
                    "time": now_str,
                    "action": "Ngắt máy bơm (Hoàn thành)",
                    "mode": mode_text,
                    "volume": volume_str,
                    "moisture": sensor_data["moisture"] if sensor_data["moisture"] is not None else "N/A",
                    "temp": sensor_data["temp"],
                    "humidity_air": sensor_data["humidity_air"],
                    "weather_desc": sensor_data["weather_desc"]
                }
                sensor_data["pump_history"].insert(0, log_entry)
                print(f"🔴 TẮT máy bơm - {volume_str} - Moisture: {sensor_data['moisture']}%, Temp: {sensor_data['temp']}°C")

            # Giới hạn tối đa 10 dòng
            if len(sensor_data["pump_history"]) > 10:
                sensor_data["pump_history"].pop()
            
            # Lưu vào JSON
            persistent_data["pump_history"] = sensor_data["pump_history"]
            print(f"📝 Entry lưu vào JSON: {log_entry}")
            save_data(persistent_data)
            
            last_pump_status = current_status
        except Exception as e:
            print(f"❌ Lỗi trong save_pump_history: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"[DEBUG] Status không thay đổi, bỏ qua lưu")

@app.route('/get-statistics')
def get_statistics():
    """API trả về thống kê theo ngày/tuần/tháng"""
    try:
        period = request.args.get('period', 'day')  # day, week, month
        
        if not os.path.exists(DATA_FILE):
            return jsonify({
                "total_water": 0,
                "pump_times": 0,
                "avg_water": 0,
                "daily_stats": [],
                "error": "Chưa có dữ liệu"
            })
        
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        pump_history = data.get('pump_history', [])
        
        if not pump_history:
            return jsonify({
                "total_water": 0,
                "pump_times": 0,
                "avg_water": 0,
                "daily_stats": [],
                "message": "Chưa có lịch sử bơm nước"
            })
        
        # --- TÍNH TOÁN THỐNG KÊ ---
        daily_stats = {}
        total_water_ml = 0
        pump_count = 0
        
        for entry in pump_history:
            if "Ngắt máy bơm" in entry.get('action', ''):
                try:
                    # Lấy ngày từ time format: "HH:MM:SS | DD/MM/YYYY"
                    time_parts = entry.get('time', '').split(' | ')
                    if len(time_parts) == 2:
                        date_str = time_parts[1]  # DD/MM/YYYY
                        
                        # Lấy lượng nước từ volume format: "123 ml (45 giây)"
                        volume_str = entry.get('volume', '0 ml').split(' ')[0]
                        water_ml = int(volume_str) if volume_str.isdigit() else 0
                        
                        total_water_ml += water_ml
                        pump_count += 1
                        
                        # Thêm vào daily_stats
                        if date_str not in daily_stats:
                            daily_stats[date_str] = {
                                "date": date_str,
                                "water": 0,
                                "times": 0,
                                "avg_moisture": 0,
                                "temp": 0,
                                "humidity_air": 0
                            }
                        
                        daily_stats[date_str]["water"] += water_ml
                        daily_stats[date_str]["times"] += 1
                        daily_stats[date_str]["avg_moisture"] = entry.get('moisture', 0)
                        daily_stats[date_str]["temp"] = entry.get('temp', 0)
                        daily_stats[date_str]["humidity_air"] = entry.get('humidity_air', 0)
                except Exception as e:
                    print(f"Lỗi parse pump_history: {e}")
                    continue
        
        # --- FILTER THEO PERIOD ---
        now = datetime.now()
        filtered_stats = []
        
        for date_str, stats in daily_stats.items():
            try:
                record_date = datetime.strptime(date_str, "%d/%m/%Y")
                
                if period == "day":
                    if record_date.date() == now.date():
                        filtered_stats.append(stats)
                elif period == "week":
                    days_diff = (now.date() - record_date.date()).days
                    if 0 <= days_diff < 7:
                        filtered_stats.append(stats)
                elif period == "month":
                    if record_date.year == now.year and record_date.month == now.month:
                        filtered_stats.append(stats)
            except:
                pass
        
        # Sắp xếp từ mới nhất
        filtered_stats.sort(key=lambda x: x['date'], reverse=True)
        
        avg_water = round(total_water_ml / pump_count) if pump_count > 0 else 0
        
        return jsonify({
            "period": period,
            "total_water": total_water_ml,
            "pump_times": pump_count,
            "avg_water": avg_water,
            "daily_stats": filtered_stats
        })
    except Exception as e:
        print(f"Lỗi /get-statistics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get-data')
def get_data():
    global last_ai_time, last_moisture_ai, cached_advice, last_pump_status, pump_start_time, persistent_data, last_sensor_update_time, sensor_connected
    
    # --- KIỂM TRA KẾT NỐI CẢM BIẾN ---
    if last_sensor_update_time is not None:
        time_since_update = time.time() - last_sensor_update_time
        if time_since_update > 30:  # Quá 30 giây không nhận dữ liệu
            sensor_connected = False
            sensor_data["sensor_connected"] = False
        else:
            sensor_connected = True
            sensor_data["sensor_connected"] = True
    else:
        # Chưa pernah nhận dữ liệu từ cảm biến
        sensor_connected = False
        sensor_data["sensor_connected"] = False
    
    weather_info = {}
    try:
        res_c = requests.get(CURRENT_URL, timeout=3).json()
        res_f = requests.get(FORECAST_URL, timeout=3).json()
        
        if str(res_c.get("cod")) == "200":
            rain_val = 0
            if "rain" in res_c:
                rain_val = res_c["rain"].get("1h", res_c["rain"].get("3h", 0))

            weather_info = {
                "temp": round(res_c['main'].get('temp', 0)),
                "desc": res_c['weather'][0].get('description', "N/A").capitalize(),
                "hum": res_c['main'].get('humidity', 0),
                "wind": res_c['wind'].get('speed', 0),
                "pres": res_c['main'].get('pressure', 0),
                "vis": res_c.get('visibility', 0) / 1000,
                "rain": rain_val,
                "next_temp": round(res_f['list'][0]['main'].get('temp', 0)) if "list" in res_f else "--",
                "next_desc": res_f['list'][0]['weather'][0].get('description', "N/A").capitalize() if "list" in res_f else "N/A",
                "next_rain_prob": round(res_f['list'][0].get('pop', 0) * 100) if "list" in res_f else 0
            }
            
            sensor_data.update({
                "temp": weather_info["temp"],
                "weather_desc": weather_info["desc"],
                "humidity_air": weather_info["hum"],
                "wind_speed": weather_info["wind"],
                "pressure": weather_info["pres"],
                "visibility": weather_info["vis"],
                "rain": weather_info["rain"],
                "next_temp": weather_info["next_temp"],
                "next_desc": weather_info["next_desc"],
                "next_rain_prob": weather_info["next_rain_prob"]
            })
    except Exception as e:
        print(f"Lỗi xử lý dữ liệu: {e}")

    # --- XỬ LÝ LOGIC ĐIỀU KHIỂN CHẶT CHẼ (CHỈ KHI CẢM BIẾN ĐƯỢC KẾT NỐI) ---
    if sensor_connected:  # Chỉ xử lý khi cảm biến đã kết nối
        if sensor_data["manual_mode"] == True:
            # 1. Chế độ điều khiển tay bằng nút bấm (đã xử lý lưu dữ liệu ở /control-pump)
            if sensor_data["pump_manual"] == "ON":
                sensor_data["ai_advice"] = "CHẾ ĐỘ TAY: Hãy bật máy bơm."
            else:
                sensor_data["ai_advice"] = "CHẾ ĐỘ TAY: Tắt máy bơm."
        else:
            # 2. Chế độ AI tự động
            current_time = time.time()
            if (current_time - last_ai_time > 600) or (sensor_data["moisture"] is not None and abs(sensor_data["moisture"] - last_moisture_ai) >= 5) or (last_ai_time == 0):
                raw_advice = get_groq_advice(sensor_data["moisture"], weather_info, CROP_DATABASE[current_crop]["name"])
                
                # Tách mã điều khiển [PUMP_ON]/[PUMP_OFF] ra khỏi nội dung phân tích văn bản
                if "[PUMP_ON]" in raw_advice:
                    sensor_data["pump_status"] = "ON"
                    cached_advice = raw_advice.replace("[PUMP_ON]", "").strip()
                elif "[PUMP_OFF]" in raw_advice:
                    sensor_data["pump_status"] = "OFF"
                    cached_advice = raw_advice.replace("[PUMP_OFF]", "").strip()
                else:
                    sensor_data["pump_status"] = "OFF"
                    cached_advice = raw_advice
                    
                last_ai_time = current_time
                last_moisture_ai = sensor_data["moisture"]
                
            sensor_data["ai_advice"] = cached_advice
            
            # Gọi logic lưu dữ liệu cho chế độ AI
            save_pump_history(sensor_data["pump_status"], False)
        
        # --- KIỂM TRA VÀ GỬI CẢNH BÁO ĐỘ ẨM ---
        # Gửi cảnh báo mỗi khi vượt/thấp hơn ngưỡng (không phải 1 lần/ngày)
        # CHỈ CHẠY KHI CẢM BIẾN ĐÃ KẾT NỐI
        try:
            global is_currently_dry, is_currently_wet
            
            if sensor_data["moisture"] is not None:
                # Kiểm tra trạng thái hiện tại
                new_is_dry = sensor_data["moisture"] < 30
                new_is_wet = sensor_data["moisture"] > 75
                
                # Gửi cảnh báo khi chuyển từ bình thường → khô
                if new_is_dry and not is_currently_dry:
                    send_alert_email("DRY", sensor_data["moisture"])
                    is_currently_dry = True
                    print(f"🚨 Cảnh báo: ĐẤT QUTRƠI KHÔNG KHI (Moisture: {sensor_data['moisture']}%)")
                
                # Gửi cảnh báo khi chuyển từ bình thường → ẩm
                if new_is_wet and not is_currently_wet:
                    send_alert_email("WET", sensor_data["moisture"])
                    is_currently_wet = True
                    print(f"🚨 Cảnh báo: ĐẤT QUTRƠI ẨM (Moisture: {sensor_data['moisture']}%)")
                
                # Gửi cảnh báo khi khôi phục từ khô → bình thường
                if not new_is_dry and is_currently_dry:
                    is_currently_dry = False
                    print(f"✅ Khôi phục: Độ ẩm bình thường (Moisture: {sensor_data['moisture']}%)")
                
                # Gửi cảnh báo khi khôi phục từ ẩm → bình thường
                if not new_is_wet and is_currently_wet:
                    is_currently_wet = False
                    print(f"✅ Khôi phục: Độ ẩm bình thường (Moisture: {sensor_data['moisture']}%)")
            else:
                # Reset flag cảnh báo khi cảm biến chưa kết nối
                is_currently_dry = False
                is_currently_wet = False
                
        except Exception as e:
            print(f"Lỗi xử lý cảnh báo: {e}")
    else:
        # Cảm biến chưa kết nối
        sensor_data["ai_advice"] = "⚠️ Cảm biến chưa kết nối. Vui lòng kiểm tra kết nối ESP32/Arduino."
        
    return jsonify(sensor_data)

@app.route('/get-alert-history')
def get_alert_history():
    """API trả về lịch sử cảnh báo"""
    try:
        alert_history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alert_history.json")
        
        if not os.path.exists(alert_history_file):
            return jsonify({"alerts": [], "message": "Chưa có cảnh báo"})
        
        with open(alert_history_file, 'r', encoding='utf-8') as f:
            alerts = json.load(f)
        
        return jsonify({"alerts": alerts})
    except Exception as e:
        print(f"Lỗi /get-alert-history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Chatbot API - Trả lời câu hỏi về cảm biến và nông nghiệp"""
    try:
        user_message = request.json.get('message', '').strip()
        
        if not user_message:
            return jsonify({"error": "Tin nhắn không được trống"}), 400
        
        # Chuẩn bị context từ dữ liệu hiện tại
        moisture_status = f"{sensor_data['moisture']}%" if sensor_data['moisture'] is not None else "CHƯA KẾT NỐI"
        
        context = f"""
        Bạn là một Trợ lý Nông nghiệp AI chuyên nghiệp cho hệ thống Smart Farm.
        
        DỮ LIỆU HỆ THỐNG HIỆN TẠI:
        - Trạng thái kết nối cảm biến: {'✅ ĐÃ KẾT NỐI' if sensor_data['sensor_connected'] else '❌ CHƯA KẾT NỐI'}
        - Độ ẩm đất: {moisture_status}
        - Nhiệt độ: {sensor_data['temp']}°C
        - Độ ẩm khí trời: {sensor_data['humidity_air']}%
        - Thời tiết: {sensor_data['weather_desc']}
        - Gió: {sensor_data['wind_speed']} m/s
        - Mưa: {sensor_data['rain']} mm
        - Áp suất: {sensor_data['pressure']} hPa
        - Chỉ số NPK: N={sensor_data['n_val']}, P={sensor_data['p_val']}, K={sensor_data['k_val']} (mg/kg)
        - Cây trồng hiện tại: {CROP_DATABASE[current_crop]['name']}
        - Trạng thái bơm: {sensor_data['pump_status']}
        - Chế độ: {'Thủ công' if sensor_data['manual_mode'] else 'Tự động (AI)'}
        
        TRẠNG THÁI CẢM BIẾN:
        - Cảm biến độ ẩm đất: {'✅ Hoạt động (đang đọc ' + moisture_status + ')' if sensor_data['sensor_connected'] else '❌ CHƯA KẾT NỐI - Vui lòng kiểm tra cáp USB hoặc WiFi'}
        - Cảm biến nhiệt độ: ✅ Hoạt động (đang đọc {sensor_data['temp']}°C)
        - Cảm biến độ ẩm khí trời: ✅ Hoạt động (đang đọc {sensor_data['humidity_air']}%)
        - Kết nối API Thời tiết: ✅ Hoạt động
        - Kết nối Firebase: ✅ Hoạt động
        
        Hãy trả lời các câu hỏi về:
        1. Trạng thái các cảm biến và hệ thống
        2. Khuyến nghị về nước tưới dựa trên dữ liệu hiện tại
        3. Lịch sử quá khứ của bệnh cây, độ ẩm, v.v.
        4. Cải thiện chỉ số NPK
        5. Các vấn đề kỹ thuật nông nghiệp
        
        Lưu ý: Trả lời ngắn gọn, chuyên nghiệp, dễ hiểu (2-3 câu).
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            max_tokens=200,
            temperature=0.5
        )
        
        bot_response = chat_completion.choices[0].message.content.strip()
        
        return jsonify({
            "success": True,
            "message": bot_response
        })
    except Exception as e:
        print(f"Lỗi chatbot: {e}")
        return jsonify({
            "success": False,
            "message": f"Lỗi xử lý: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)