import json
import requests
from datetime import datetime

class NutritionAnalyzer:
    def __init__(self, nutrition_db_path):
  
        self.nutrition_db_path = nutrition_db_path
        self.nutrition_data = {}
        self.load_nutrition_database()
        
        # API configuration (optional for external nutrition APIs)
        self.api_key = None  # Set this if using external APIs
        self.use_external_api = False
        
        print("Nutrition analyzer initialized")
    
    def load_nutrition_database(self):
        """Load nutrition database from JSON file"""
        try:
            with open(self.nutrition_db_path, 'r') as f:
                self.nutrition_data = json.load(f)
            print(f"Loaded {len(self.nutrition_data)} food items from database")
        except FileNotFoundError:
            print("Nutrition database not found, creating default database")
            self.create_default_database()
        except Exception as e:
            print(f"Error loading nutrition database: {e}")
            self.create_default_database()
    
    def create_default_database(self):
        """Create default nutrition database with common foods"""
        self.nutrition_data = {
            # Fruits (per 100g)
            "apple": {
                "name": "Apple",
                "category": "fruit",
                "calories": 52,
                "protein": 0.3,
                "carbs": 14,
                "fat": 0.2,
                "fiber": 2.4,
                "sugar": 10.4,
                "sodium": 1,
                "potassium": 107,
                "vitamin_c": 4.6,
                "calcium": 6,
                "iron": 0.12
            },
            "banana": {
                "name": "Banana",
                "category": "fruit",
                "calories": 89,
                "protein": 1.1,
                "carbs": 23,
                "fat": 0.3,
                "fiber": 2.6,
                "sugar": 12.2,
                "sodium": 1,
                "potassium": 358,
                "vitamin_c": 8.7,
                "calcium": 5,
                "iron": 0.26
            },
            "orange": {
                "name": "Orange",
                "category": "fruit",
                "calories": 47,
                "protein": 0.9,
                "carbs": 12,
                "fat": 0.1,
                "fiber": 2.4,
                "sugar": 9.4,
                "sodium": 0,
                "potassium": 181,
                "vitamin_c": 53.2,
                "calcium": 40,
                "iron": 0.1
            },
            
            # Vegetables (per 100g)
            "tomato": {
                "name": "Tomato",
                "category": "vegetable",
                "calories": 18,
                "protein": 0.9,
                "carbs": 3.9,
                "fat": 0.2,
                "fiber": 1.2,
                "sugar": 2.6,
                "sodium": 5,
                "potassium": 237,
                "vitamin_c": 13.7,
                "calcium": 10,
                "iron": 0.27
            },
            "carrot": {
                "name": "Carrot",
                "category": "vegetable",
                "calories": 41,
                "protein": 0.9,
                "carbs": 10,
                "fat": 0.2,
                "fiber": 2.8,
                "sugar": 4.7,
                "sodium": 69,
                "potassium": 320,
                "vitamin_c": 5.9,
                "calcium": 33,
                "iron": 0.3,
                "vitamin_a": 835
            },
            "broccoli": {
                "name": "Broccoli",
                "category": "vegetable",
                "calories": 25,
                "protein": 3,
                "carbs": 5,
                "fat": 0.4,
                "fiber": 3,
                "sugar": 1.5,
                "sodium": 33,
                "potassium": 288,
                "vitamin_c": 89.2,
                "calcium": 47,
                "iron": 0.73
            },
            
            # Proteins (per 100g)
            "chicken_breast": {
                "name": "Chicken Breast",
                "category": "protein",
                "calories": 165,
                "protein": 31,
                "carbs": 0,
                "fat": 3.6,
                "fiber": 0,
                "sugar": 0,
                "sodium": 74,
                "potassium": 256,
                "calcium": 15,
                "iron": 0.89
            },
            "salmon": {
                "name": "Salmon",
                "category": "protein",
                "calories": 208,
                "protein": 20,
                "carbs": 0,
                "fat": 13,
                "fiber": 0,
                "sugar": 0,
                "sodium": 59,
                "potassium": 363,
                "calcium": 9,
                "iron": 0.25,
                "omega_3": 2.3
            },
            
            # Grains (per 100g)
            "white_rice": {
                "name": "White Rice (cooked)",
                "category": "grain",
                "calories": 130,
                "protein": 2.7,
                "carbs": 28,
                "fat": 0.3,
                "fiber": 0.4,
                "sugar": 0.05,
                "sodium": 1,
                "potassium": 35,
                "calcium": 28,
                "iron": 0.2
            },
            "brown_rice": {
                "name": "Brown Rice (cooked)",
                "category": "grain",
                "calories": 112,
                "protein": 2.6,
                "carbs": 23,
                "fat": 0.9,
                "fiber": 1.8,
                "sugar": 0.4,
                "sodium": 1,
                "potassium": 43,
                "calcium": 23,
                "iron": 0.4
            },
            "bread": {
                "name": "White Bread",
                "category": "grain",
                "calories": 265,
                "protein": 9,
                "carbs": 49,
                "fat": 3.2,
                "fiber": 2.7,
                "sugar": 5.67,
                "sodium": 477,
                "potassium": 100,
                "calcium": 149,
                "iron": 3.36
            },
            
            # Dairy (per 100g)
            "milk": {
                "name": "Whole Milk",
                "category": "dairy",
                "calories": 61,
                "protein": 3.4,
                "carbs": 5,
                "fat": 3.3,
                "fiber": 0,
                "sugar": 5,
                "sodium": 40,
                "potassium": 132,
                "vitamin_c": 0,
                "calcium": 113,
                "iron": 0.03
            },
            "cheese": {
                "name": "Cheddar Cheese",
                "category": "dairy",
                "calories": 402,
                "protein": 25,
                "carbs": 1.3,
                "fat": 33,
                "fiber": 0,
                "sugar": 0.5,
                "sodium": 621,
                "potassium": 98,
                "calcium": 721,
                "iron": 0.68
            },
            
            # Default/Unknown
            "unknown": {
                "name": "Unknown Food",
                "category": "unknown",
                "calories": 150,
                "protein": 5,
                "carbs": 20,
                "fat": 5,
                "fiber": 2,
                "sugar": 5,
                "sodium": 100,
                "potassium": 200,
                "calcium": 50,
                "iron": 1
            }
        }
        
        # Save default database
        self.save_nutrition_database()
    
    def save_nutrition_database(self):
        """Save nutrition database to JSON file"""
        try:
            with open(self.nutrition_db_path, 'w') as f:
                json.dump(self.nutrition_data, f, indent=2)
            print("Nutrition database saved")
        except Exception as e:
            print(f"Error saving nutrition database: {e}")
    
    def get_food_info(self, food_item):
        """
        Get nutritional information for a food item
        
        Args:
            food_item (str): Food item name
            
        Returns:
            dict: Nutritional information per 100g
        """
        food_item = food_item.lower().strip()
        
        # Direct match
        if food_item in self.nutrition_data:
            return self.nutrition_data[food_item].copy()
        
        # Partial match
        for key in self.nutrition_data.keys():
            if food_item in key or key in food_item:
                return self.nutrition_data[key].copy()
        
        # Try external API if configured
        if self.use_external_api and self.api_key:
            external_data = self.fetch_from_external_api(food_item)
            if external_data:
                return external_data
        
        # Return unknown food data as fallback
        print(f"Food item '{food_item}' not found, using unknown food data")
        return self.nutrition_data['unknown'].copy()
    
    def calculate_nutrition(self, food_item, weight_grams):
        """
        Calculate nutrition for specific weight
        
        Args:
            food_item (str): Food item name
            weight_grams (float): Weight in grams
            
        Returns:
            dict: Calculated nutritional information
        """
        if weight_grams <= 0:
            return None
        
        # Get base nutrition info (per 100g)
        base_nutrition = self.get_food_info(food_item)
        if not base_nutrition:
            return None
        
        # Calculate scaling factor
        scale_factor = weight_grams / 100.0
        
        # Scale all nutritional values
        calculated_nutrition = {
            'food_item': base_nutrition['name'],
            'category': base_nutrition['category'],
            'weight_grams': round(weight_grams, 1),
            'calories': round(base_nutrition['calories'] * scale_factor, 1),
            'protein': round(base_nutrition['protein'] * scale_factor, 2),
            'carbs': round(base_nutrition['carbs'] * scale_factor, 2),
            'fat': round(base_nutrition['fat'] * scale_factor, 2),
            'fiber': round(base_nutrition['fiber'] * scale_factor, 2),
            'sugar': round(base_nutrition['sugar'] * scale_factor, 2),
            'sodium': round(base_nutrition['sodium'] * scale_factor, 1),
            'potassium': round(base_nutrition['potassium'] * scale_factor, 1),
            'calcium': round(base_nutrition['calcium'] * scale_factor, 1),
            'iron': round(base_nutrition['iron'] * scale_factor, 3),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add optional nutrients if present
        optional_nutrients = ['vitamin_c', 'vitamin_a', 'omega_3']
        for nutrient in optional_nutrients:
            if nutrient in base_nutrition:
                calculated_nutrition[nutrient] = round(
                    base_nutrition[nutrient] * scale_factor, 2
                )
        
        return calculated_nutrition
    
    def fetch_from_external_api(self, food_item):
        """
        Fetch nutrition data from external API (e.g., USDA, Edamam)
        This is a placeholder implementation
        
        Args:
            food_item (str): Food item name
            
        Returns:
            dict: Nutritional information or None
        """
        try:
            # Example implementation for USDA FoodData Central API
            # You would need to sign up for an API key
            if not self.api_key:
                return None
            
            url = "https://api.nal.usda.gov/fdc/v1/foods/search"
            params = {
                'query': food_item,
                'api_key': self.api_key,
                'pageSize': 1
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                if data.get('foods'):
                    food_data = data['foods'][0]
                    nutrients = food_data.get('foodNutrients', [])
                    
                    # Parse nutrients (this would need more detailed mapping)
                    nutrition_info = {
                        'name': food_data.get('description', food_item),
                        'category': 'external_api',
                        'calories': 0,
                        'protein': 0,
                        'carbs': 0,
                        'fat': 0,
                        'fiber': 0,
                        'sugar': 0,
                        'sodium': 0,
                        'potassium': 0,
                        'calcium': 0,
                        'iron': 0
                    }
                    
                    # Map API nutrients to our format
                    nutrient_mapping = {
                        'Energy': 'calories',
                        'Protein': 'protein',
                        'Carbohydrate, by difference': 'carbs',
                        'Total lipid (fat)': 'fat',
                        'Fiber, total dietary': 'fiber',
                        'Sugars, total including NLEA': 'sugar',
                        'Sodium, Na': 'sodium',
                        'Potassium, K': 'potassium',
                        'Calcium, Ca': 'calcium',
                        'Iron, Fe': 'iron'
                    }
                    
                    for nutrient in nutrients:
                        nutrient_name = nutrient.get('nutrientName', '')
                        if nutrient_name in nutrient_mapping:
                            key = nutrient_mapping[nutrient_name]
                            nutrition_info[key] = nutrient.get('value', 0)
                    
                    return nutrition_info
                    
        except Exception as e:
            print(f"External API error: {e}")
        
        return None
    
    def add_custom_food(self, food_name, nutrition_info):
        """
        Add custom food to database
        
        Args:
            food_name (str): Food name
            nutrition_info (dict): Nutritional information per 100g
        """
        food_name = food_name.lower().strip()
        self.nutrition_data[food_name] = nutrition_info
        self.save_nutrition_database()
        print(f"Added custom food: {food_name}")
    
    def get_daily_values_percentage(self, nutrition_data):
        """
        Calculate percentage of daily values
        Based on FDA recommended daily values for adults
        
        Args:
            nutrition_data (dict): Calculated nutrition data
            
        Returns:
            dict: Percentage of daily values
        """
        daily_values = {
            'calories': 2000,
            'protein': 50,      # grams
            'carbs': 300,       # grams
            'fat': 65,          # grams
            'fiber': 25,        # grams
            'sodium': 2300,     # mg
            'potassium': 4700,  # mg
            'calcium': 1000,    # mg
            'iron': 18,         # mg
            'vitamin_c': 90     # mg
        }
        
        percentages = {}
        for nutrient, daily_value in daily_values.items():
            if nutrient in nutrition_data:
                value = nutrition_data[nutrient]
                # Convert sodium, potassium, calcium from mg to match our database
                if nutrient in ['sodium', 'potassium', 'calcium']:
                    value = value  # Our database is already in mg
                
                percentage = (value / daily_value) * 100
                percentages[f"{nutrient}_dv"] = round(percentage, 1)
        
        return percentages
    
    def get_nutrition_summary(self, food_item, weight_grams):
        """
        Get complete nutrition summary including daily values
        
        Args:
            food_item (str): Food item name
            weight_grams (float): Weight in grams
            
        Returns:
            dict: Complete nutrition summary
        """
        nutrition = self.calculate_nutrition(food_item, weight_grams)
        if not nutrition:
            return None
        
        daily_values = self.get_daily_values_percentage(nutrition)
        
        # Combine nutrition data with daily value percentages
        summary = {**nutrition, **daily_values}
        
        return summary


# Test script
if __name__ == '__main__':
    import sys
    
    analyzer = NutritionAnalyzer('data/nutrition_db.json')
    
    if len(sys.argv) >= 3:
        food_item = sys.argv[1]
        weight = float(sys.argv[2])
        
        print(f"=== Nutrition Analysis ===")
        print(f"Food: {food_item}")
        print(f"Weight: {weight}g")
        print()
        
        summary = analyzer.get_nutrition_summary(food_item, weight)
        if summary:
            print(f"Food Item: {summary['food_item']}")
            print(f"Category: {summary['category']}")
            print(f"Weight: {summary['weight_grams']}g")
            print()
            print("Macronutrients:")
            print