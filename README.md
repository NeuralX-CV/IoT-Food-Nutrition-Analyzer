# IoT Food Nutrition Analyzer

A smart IoT system that combines weight measurement and computer vision to analyze food items and provide detailed nutritional information. Built for Raspberry Pi 5 with HX711 load cell amplifier and webcam.

## 🚀 Features

- **Real-time Weight Measurement**: Precision weighing using HX711 load cell amplifier
- **Food Recognition**: Computer vision-based food detection and classification
- **Nutritional Analysis**: Automatic calorie and nutrition calculation based on weight and food type
- **Web Interface**: Real-time dashboard for monitoring and results
- **Data Logging**: Historical data storage and analysis


## 📋 Hardware Requirements

- Raspberry Pi 5 (4GB+ RAM recommended)
- HX711 Load Cell Amplifier
- Load Cell (5-50kg capacity recommended)
- USB Webcam or Raspberry Pi Camera Module 3
- MicroSD Card (32GB+ Class 10)
- Power Supply (5V 3A USB-C)

## 🔧 Hardware Connections

### HX711 to Raspberry Pi 5
```
HX711    →    Raspberry Pi 5
VCC      →    5V (Pin 2)
GND      →    GND (Pin 6)
DT       →    GPIO 5 (Pin 29)
SCK      →    GPIO 6 (Pin 31)
```

### Load Cell to HX711
```
Load Cell    →    HX711
Red          →    E+
Black        →    E-
White        →    A-
Green        →    A+
```

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/NeuralX-CV/IoT-Food-Nutrition-Analyzer.git
cd iot-food-nutrition-analyzer
```

### 2. Run Setup Script
```bash
chmod +x setup.sh
./setup.sh
```

### 3. Manual Installation (Alternative)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
pip3 install -r requirements.txt

# Install system dependencies
sudo apt install -y python3-opencv python3-numpy python3-scipy

# Enable camera (if using Pi Camera)
sudo raspi-config
# Navigate to Interface Options > Camera > Enable
```

## 📦 Dependencies

```txt
# requirements.txt
Flask==2.3.3
opencv-python==4.8.1.78
numpy==1.24.3
scipy==1.11.2
RPi.GPIO==0.7.1
tensorflow==2.13.0
Pillow==10.0.0
requests==2.31.0
sqlite3
```

## 🔧 Configuration

### config.py
```python
# Hardware Configuration
HX711_DT_PIN = 5
HX711_SCK_PIN = 6
CAMERA_INDEX = 0  # 0 for USB webcam, or path for Pi Camera

# Model Configuration
MODEL_PATH = "models/food_model.h5"
CONFIDENCE_THRESHOLD = 0.7

# Web Interface
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
DEBUG_MODE = True

# Database
DATABASE_PATH = "data/measurements.db"
NUTRITION_DB_PATH = "data/nutrition_db.json"

# Calibration
CALIBRATION_FACTOR = 2280.0  # Adjust based on your load cell
TARE_OFFSET = 0
```

## 🏃‍♂️ Usage

### 1. Calibrate the Scale
```bash
python3 src/calibrate_scale.py
```

### 2. Start the Application
```bash
python3 src/main.py
```

### 3. Access Web Interface
Open your browser and navigate to:
```
http://raspberry-pi-ip:5000
```

### 4. API Endpoints
```bash
# Get current measurement
GET /api/measure

# Get nutrition info
GET /api/nutrition/<food_item>

# Get historical data
GET /api/history
```

## 🧠 Food Recognition Model

The project uses a pre-trained TensorFlow model for food classification. You can:

1. **Use the included model**: Basic food recognition for common items
2. **Train your own model**: Follow the training guide in `docs/model_training.md`
3. **Use cloud APIs**: Integrate with Google Vision API or similar services

### Supported Food Categories
- Fruits (apple, banana, orange, etc.)
- Vegetables (carrot, broccoli, tomato, etc.)
- Proteins (chicken, beef, fish, etc.)
- Grains (rice, bread, pasta, etc.)
- Dairy (milk, cheese, yogurt, etc.)

## 📊 Nutrition Database

The nutrition database (`data/nutrition_db.json`) contains nutritional information per 100g for various foods:

```json
{
  "apple": {
    "calories": 52,
    "protein": 0.3,
    "carbs": 14,
    "fat": 0.2,
    "fiber": 2.4,
    "sugar": 10.4,
    "vitamin_c": 4.6
  }
}
```

## 🖥️ Web Interface Features

- **Live Camera Feed**: Real-time video stream with food detection overlay
- **Weight Display**: Current weight reading with tare function
- **Nutrition Panel**: Detailed nutritional breakdown
- **History Graph**: Weight and nutrition trends over time
- **Settings**: Calibration and configuration options

## 🔄 Systemd Service

To run as a system service:

```bash
# Copy service file
sudo cp systemd/nutrition-analyzer.service /etc/systemd/system/

# Enable and start service
sudo systemctl enable nutrition-analyzer.service
sudo systemctl start nutrition-analyzer.service

# Check status
sudo systemctl status nutrition-analyzer.service
```

## 🛠️ Troubleshooting

### Weight Sensor Issues
```bash
# Check connections
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup([5,6], GPIO.OUT)"

# Test HX711 communication
python3 src/test_weight_sensor.py
```

### Camera Issues
```bash
# List available cameras
ls /dev/video*

# Test camera
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.read()[0])"
```

### Model Loading Issues
```bash
# Verify TensorFlow installation
python3 -c "import tensorflow as tf; print(tf.__version__)"

# Check model file
ls -la models/food_model.h5
```

## 📈 Performance Optimization

### For Raspberry Pi 5:
- Use GPU acceleration for TensorFlow operations
- Optimize camera resolution (640x480 recommended)
- Enable memory split for GPU: `sudo raspi-config` → Advanced → Memory Split → 128

### Model Optimization:
- Use TensorFlow Lite for faster inference
- Quantize model to INT8 for speed improvements
- Reduce input image resolution for real-time processing


