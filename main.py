#!/usr/bin/env python3
import threading
import time
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from weight_sensor import WeightSensor
from food_detection import FoodDetector
from nutrition_analyzer import NutritionAnalyzer
from config import *

class NutritionAnalyzerApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'your-secret-key-change-this'
        self.weight_sensor = WeightSensor(HX711_DT_PIN, HX711_SCK_PIN)
        self.food_detector = FoodDetector(CAMERA_INDEX, MODEL_PATH)
        self.nutrition_analyzer = NutritionAnalyzer(NUTRITION_DB_PATH)
        self.current_weight = 0.0
        self.detected_food = None
        self.nutrition_data = None
        self.is_measuring = False
        self.init_database()
        self.setup_routes()
        self.monitoring_thread = threading.Thread(target=self.monitor_sensors, daemon=True)
        self.monitoring_thread.start()
        print("Nutrition Analyzer initialized successfully!")

    def init_database(self):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                weight REAL,
                food_item TEXT,
                calories REAL,
                protein REAL,
                carbs REAL,
                fat REAL,
                confidence REAL
            )
        ''')
        conn.commit()
        conn.close()

    def monitor_sensors(self):
        while True:
            try:
                self.current_weight = self.weight_sensor.get_weight()
                if self.current_weight > 0.01:
                    if not self.is_measuring:
                        self.is_measuring = True
                        detection_result = self.food_detector.detect_food()
                        if detection_result and detection_result['confidence'] > CONFIDENCE_THRESHOLD:
                            self.detected_food = detection_result['food_item']
                            self.nutrition_data = self.nutrition_analyzer.calculate_nutrition(
                                self.detected_food,
                                self.current_weight * 1000
                            )
                            self.save_measurement()
                else:
                    self.is_measuring = False
                    self.detected_food = None
                    self.nutrition_data = None
                time.sleep(0.5)
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(1)

    def save_measurement(self):
        if self.nutrition_data:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO measurements 
                (timestamp, weight, food_item, calories, protein, carbs, fat, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                self.current_weight,
                self.detected_food,
                self.nutrition_data['calories'],
                self.nutrition_data['protein'],
                self.nutrition_data['carbs'],
                self.nutrition_data['fat'],
                self.food_detector.last_confidence
            ))
            conn.commit()
            conn.close()

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route('/dashboard')
        def dashboard():
            return render_template('dashboard.html')

        @self.app.route('/api/status')
        def api_status():
            return jsonify({
                'weight': round(self.current_weight, 3),
                'food_item': self.detected_food,
                'nutrition': self.nutrition_data,
                'is_measuring': self.is_measuring,
                'timestamp': datetime.now().isoformat()
            })

        @self.app.route('/api/tare', methods=['POST'])
        def api_tare():
            try:
                self.weight_sensor.tare()
                return jsonify({'success': True, 'message': 'Scale tared successfully'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/calibrate', methods=['POST'])
        def api_calibrate():
            try:
                known_weight = float(request.json.get('weight', 0))
                if known_weight <= 0:
                    return jsonify({'success': False, 'error': 'Invalid weight value'})
                self.weight_sensor.calibrate(known_weight)
                return jsonify({'success': True, 'message': f'Calibrated with {known_weight}kg'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/history')
        def api_history():
            try:
                limit = request.args.get('limit', 50, type=int)
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM measurements 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                rows = cursor.fetchall()
                conn.close()
                history = []
                for row in rows:
                    history.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'weight': row[2],
                        'food_item': row[3],
                        'calories': row[4],
                        'protein': row[5],
                        'carbs': row[6],
                        'fat': row[7],
                        'confidence': row[8]
                    })
                return jsonify(history)
            except Exception as e:
                return jsonify({'error': str(e)})

        @self.app.route('/api/camera/stream')
        def camera_stream():
            return self.food_detector.generate_stream()

        @self.app.route('/api/nutrition/<food_item>')
        def api_nutrition_info(food_item):
            try:
                weight = request.args.get('weight', 100, type=float)
                nutrition = self.nutrition_analyzer.calculate_nutrition(food_item, weight)
                if nutrition:
                    return jsonify(nutrition)
                else:
                    return jsonify({'error': 'Food item not found in database'})
            except Exception as e:
                return jsonify({'error': str(e)})

    def run(self):
        print(f"Starting Nutrition Analyzer on {FLASK_HOST}:{FLASK_PORT}")
        self.app.run(host=FLASK_HOST, port=FLASK_PORT, debug=DEBUG_MODE, threaded=True)

    def cleanup(self):
        print("Shutting down Nutrition Analyzer...")
        if hasattr(self, 'weight_sensor'):
            self.weight_sensor.cleanup()
        if hasattr(self, 'food_detector'):
            self.food_detector.cleanup()

if __name__ == '__main__':
    analyzer = None
    try:
        analyzer = NutritionAnalyzerApp()
        analyzer.run()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Critical error: {e}")
    finally:
        if analyzer:
            analyzer.cleanup()
