import time
import json
import statistics
import RPi.GPIO as GPIO
from config import CALIBRATION_FACTOR, TARE_OFFSET

class WeightSensor:
    def __init__(self, dt_pin, sck_pin):
        """
        Initialize HX711 weight sensor
        
        Args:
            dt_pin (int): Data pin (DT)
            sck_pin (int): Clock pin (SCK)
        """
        self.dt_pin = dt_pin
        self.sck_pin = sck_pin
        self.calibration_factor = CALIBRATION_FACTOR
        self.tare_offset = TARE_OFFSET
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.dt_pin, GPIO.IN)
        GPIO.setup(self.sck_pin, GPIO.OUT)
        
        # Initialize
        self.power_up()
        self.load_calibration()
        
        print(f"HX711 initialized on pins DT:{dt_pin}, SCK:{sck_pin}")
    
    def load_calibration(self):
        """Load calibration data from file"""
        try:
            with open('data/calibration.json', 'r') as f:
                cal_data = json.load(f)
                self.calibration_factor = cal_data.get('calibration_factor', CALIBRATION_FACTOR)
                self.tare_offset = cal_data.get('tare_offset', TARE_OFFSET)
                print(f"Loaded calibration: factor={self.calibration_factor}, offset={self.tare_offset}")
        except FileNotFoundError:
            print("No calibration file found, using defaults")
            self.save_calibration()
    
    def save_calibration(self):
        """Save calibration data to file"""
        try:
            cal_data = {
                'calibration_factor': self.calibration_factor,
                'tare_offset': self.tare_offset,
                'timestamp': time.time()
            }
            with open('data/calibration.json', 'w') as f:
                json.dump(cal_data, f, indent=2)
            print("Calibration data saved")
        except Exception as e:
            print(f"Error saving calibration: {e}")
    
    def is_ready(self):
        """Check if HX711 is ready for reading"""
        return GPIO.input(self.dt_pin) == 0
    
    def wait_ready(self, timeout=1.0):
        """Wait for HX711 to be ready"""
        start_time = time.time()
        while not self.is_ready():
            if time.time() - start_time > timeout:
                raise TimeoutError("HX711 not ready within timeout")
            time.sleep(0.001)
    
    def read_raw(self):
        """Read raw 24-bit value from HX711"""
        self.wait_ready()
        
        # Start conversion by pulling SCK high
        data = 0
        
        # Read 24 bits
        for i in range(24):
            GPIO.output(self.sck_pin, GPIO.HIGH)
            data = data << 1
            
            if GPIO.input(self.dt_pin):
                data += 1
                
            GPIO.output(self.sck_pin, GPIO.LOW)
        
        # Send one more pulse to set gain to 128 for next reading
        GPIO.output(self.sck_pin, GPIO.HIGH)
        GPIO.output(self.sck_pin, GPIO.LOW)
        
        # Convert to signed 24-bit integer
        if data & 0x800000:
            data = data | (~0xFFFFFF)
        
        return data
    
    def read_average(self, samples=10):
        """Read average of multiple samples"""
        readings = []
        
        for _ in range(samples):
            try:
                reading = self.read_raw()
                readings.append(reading)
                time.sleep(0.01)  # Small delay between readings
            except Exception as e:
                print(f"Error reading sample: {e}")
                continue
        
        if not readings:
            raise RuntimeError("No valid readings obtained")
        
        # Remove outliers using median filtering
        if len(readings) >= 3:
            readings.sort()
            # Remove top and bottom 20%
            trim = len(readings) // 5
            if trim > 0:
                readings = readings[trim:-trim]
        
        return statistics.mean(readings)
    
    def get_weight(self, samples=5):
        """
        Get weight in kilograms
        
        Args:
            samples (int): Number of samples to average
            
        Returns:
            float: Weight in kilograms
        """
        try:
            raw_reading = self.read_average(samples)
            
            # Apply tare offset
            tared_reading = raw_reading - self.tare_offset
            
            # Convert to weight using calibration factor
            weight_kg = tared_reading / self.calibration_factor
            
            # Filter out very small weights (noise)
            if abs(weight_kg) < 0.001:  # Less than 1 gram
                weight_kg = 0.0
            
            return max(0.0, weight_kg)  # Ensure non-negative
            
        except Exception as e:
            print(f"Error reading weight: {e}")
            return 0.0
    
    def tare(self, samples=20):
        """
        Tare the scale (set current reading as zero point)
        
        Args:
            samples (int): Number of samples for tare reading
        """
        print("Taring scale... Please ensure scale is empty")
        time.sleep(2)  # Give time to remove items
        
        try:
            self.tare_offset = self.read_average(samples)
            self.save_calibration()
            print(f"Scale tared. New offset: {self.tare_offset}")
        except Exception as e:
            print(f"Error during tare: {e}")
            raise
    
    def calibrate(self, known_weight_kg, samples=20):
        """
        Calibrate the scale with a known weight
        
        Args:
            known_weight_kg (float): Known weight in kilograms
            samples (int): Number of samples for calibration
        """
        print(f"Calibrating with {known_weight_kg}kg...")
        print("Please place the known weight on the scale")
        time.sleep(3)  # Give time to place weight
        
        try:
            raw_reading = self.read_average(samples)
            tared_reading = raw_reading - self.tare_offset
            
            if abs(tared_reading) < 100:  # Very small reading
                raise ValueError("Reading too small for calibration")
            
            self.calibration_factor = tared_reading / known_weight_kg
            self.save_calibration()
            
            print(f"Calibration complete. Factor: {self.calibration_factor}")
            
            # Verify calibration
            time.sleep(1)
            measured_weight = self.get_weight()
            error = abs(measured_weight - known_weight_kg) / known_weight_kg * 100
            print(f"Verification: Expected={known_weight_kg}kg, Measured={measured_weight:.3f}kg, Error={error:.1f}%")
            
        except Exception as e:
            print(f"Error during calibration: {e}")
            raise
    
    def power_down(self):
        """Power down the HX711"""
        GPIO.output(self.sck_pin, GPIO.HIGH)
        time.sleep(0.01)
    
    def power_up(self):
        """Power up the HX711"""
        GPIO.output(self.sck_pin, GPIO.LOW)
        time.sleep(0.01)
    
    def reset(self):
        """Reset the HX711"""
        self.power_down()
        self.power_up()
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        try:
            self.power_down()
            GPIO.cleanup([self.dt_pin, self.sck_pin])
            print("Weight sensor cleanup complete")
        except Exception as e:
            print(f"Error during cleanup: {e}")


# Test and calibration script
if __name__ == '__main__':
    import sys
    
    # Configuration
    DT_PIN = 5
    SCK_PIN = 6
    
    sensor = WeightSensor(DT_PIN, SCK_PIN)
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == 'calibrate':
            # Calibration mode
            print("=== Weight Sensor Calibration ===")
            
            # Step 1: Tare
            input("Remove all items from scale and press Enter to tare...")
            sensor.tare()
            
            # Step 2: Calibrate
            weight_str = input("Enter known calibration weight in kg (e.g., 1.0): ")
            known_weight = float(weight_str)
            
            input(f"Place {known_weight}kg on scale and press Enter...")
            sensor.calibrate(known_weight)
            
            print("Calibration complete!")
        
        else:
            # Continuous reading mode
            print("=== Weight Sensor Test ===")
            print("Reading weights... Press Ctrl+C to stop")
            
            while True:
                weight = sensor.get_weight()
                print(f"Weight: {weight:.3f} kg ({weight*1000:.1f} g)", end='\r')
                time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sensor.cleanup()