from flask import Flask, request, render_template, redirect, url_for
from PIL import Image
import pytesseract
import cv2
import numpy as np
import re
import sqlite3
from rapidfuzz import process
from rapidfuzz import fuzz
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'food_db.db'

pytesseract.pytesseract.tesseract_cmd = r'../Tesseract-OCR\tesseract.exe'



# Dictionary for food abbreviations.
food_dict = {
    "CDBY": "Cadbury",
    "SLT": "Salted",
    "CRML": "Caramel",
    "FNGER": "Finger",
}

#Replacing the food abbreviations with actual name.
def expand_abbreviations(text, food_dict):
   
    words = text.split()
    expanded = []
    for word in words:
        clean_word = re.sub(r'[^\w]', '', word).upper()
        if clean_word in food_dict:
            expanded.append(food_dict[clean_word])
        else:
            expanded.append(word)
    return " ".join(expanded)

# removing measurements
def remove_measurements(text):
    return re.sub(r'\b\d+\s*[a-zA-Z]+\b', '', text).strip()

def extract_food_items_from_receipt(image_stream):
    img = Image.open(image_stream)
    
    # Converting to grayscale using PIL
    gray_img = img.convert('L')
    
    # Converting PIL image to NumPy array for OpenCV processing
    gray_cv = np.array(gray_img)
    
    #applying Gaussian Blur
    blurred_cv = cv2.GaussianBlur(gray_cv, (7, 5), 0)
    
    #applying Adaptive Thresholding
    adaptive_thresh = cv2.adaptiveThreshold(
        blurred_cv, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 5
    )
    
    ocr_text = pytesseract.image_to_string(Image.fromarray(adaptive_thresh), config="--psm 4")
    
    # Splitting OCR text into lines and removing empty ones.
    lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
    
    # Regex pattern to extract food name and price.
    pattern = re.compile(r'^[\*]?(.*?)\s*£(\d+[.,]\d{2})$', re.IGNORECASE)
    
    # Keywords to filter out key words.
    filter_keywords = ['balance due', 'visa debit', 'total', 'point', 'change']
    
    food_items = []
    for line in lines:

        if any(keyword in line.lower() for keyword in filter_keywords):
            continue
        
        match = pattern.search(line)
        if match:
            item_name = match.group(1).strip()

            # if i instead of 1 in measurement convert to 1
            item_name = re.sub(r'\bi(\d+G)\b', r'1\1', item_name)

            # Clean the product name by expanding abbreviations, removing measurements.
            item_name = expand_abbreviations(item_name, food_dict).lower()
            item_name = remove_measurements(item_name)
            food_items.append(item_name)
    
    return food_items


def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def get_expirydate():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, expirydate FROM FoodDatabase")
    rows = cursor.fetchall()
    conn.close()
    db_items = [(row['name'], row['expirydate']) for row in rows]
    print("FoodDatabase items:", db_items)
    return db_items

#fuzzy matching to find the best match from the food database using 70 threshold
def match_food_item(ocr_item, food_db_items, threshold=70):
    match = process.extractOne(ocr_item, [item[0] for item in food_db_items], scorer=fuzz.token_sort_ratio)
    
    if match:
        best_match = match[0] 
        score = match[1]
        
        print(f"Match for OCR item '{ocr_item}': Best match = '{best_match}', Score = {score:.1f}")
        if score >= threshold:
            expiry_date = next(item[1] for item in food_db_items if item[0] == best_match)
            return best_match, expiry_date, score
        else:
            print(f"No good match for OCR item '{ocr_item}' (score: {score:.1f})")
            return None, None, score
    

#adding food item to pantry
def add_item_to_pantry(item_name, expiry_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Pantry (name, expirydate) VALUES (?, ?)", (item_name, expiry_date))
    conn.commit()
    conn.close()
    print(f"Inserted '{item_name}' with expiry '{expiry_date}' into Pantry.")

#getting food items from pantry
def get_pantry_contents():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, expirydate FROM Pantry ORDER BY expirydate ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows


#retrieving food items that will expire soon in ascending order
def get_expiring_notifications(threshold=30):
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().date()
    threshold_date = today + timedelta(days=threshold)
    cursor.execute("SELECT name, expirydate FROM Pantry")
    rows = cursor.fetchall()
    conn.close()
    
    notifications = []
    for row in rows:
        try:
            expiry_date = datetime.strptime(row['expirydate'], '%Y-%m-%d').date()
            if today <= expiry_date <= threshold_date:
                days_left = (expiry_date - today).days
                notifications.append((row['name'], days_left))
        except Exception as e:
            print("Error parsing expiry date for", row['name'], ":", e)
    

    notifications.sort(key=lambda x: x[1])
    
    
    formatted_notifications = [
        f"{name} will expire in {days_left} day{'s' if days_left != 1 else ''}."
        for name, days_left in notifications
    ]
    
    return formatted_notifications

# index for user to upload receipt to process, display pantry contents and displays notifications for 
#items about to expire
@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'receipt' not in request.files or request.files['receipt'].filename == '':
            return redirect(request.url)
        image_file = request.files['receipt']
        
        # Extract food items from receipt
        extracted_fooditems = extract_food_items_from_receipt(image_file.stream)
        print("Extracted items:", extracted_fooditems)
        
        # Get FoodDatabase items
        food_db_items = get_expirydate()
        
        matched_items = []
        unmatched_items = []
        
        for item in extracted_fooditems:
            matched_name, expiry_date, score = match_food_item(item, food_db_items)
            if matched_name:
                add_item_to_pantry(matched_name, expiry_date)
                matched_items.append((matched_name, expiry_date))
            else:
                unmatched_items.append(item)
        
        pantry_contents = get_pantry_contents()
        print("Current Pantry Contents:", pantry_contents)
        return render_template('pantry.html', pantry_contents=pantry_contents, unmatched_items=unmatched_items)
    
    
    pantry_contents = get_pantry_contents()
    total_items = len(pantry_contents)
    notifications = get_expiring_notifications(threshold=30)
    return render_template('index.html', pantry_contents=pantry_contents, 
                           total_items=total_items, notifications=notifications)


# displays the list of items currently in users pantry in pantry page
@app.route("/pantry")
def pantry():
    pantry_contents = get_pantry_contents()
    return render_template('pantry.html', pantry_contents=pantry_contents)

# to update details of food item in pantry to then update the database
@app.route("/edit/<int:item_id>", methods=["POST"])
def edit(item_id):
    new_name = request.form["name"]
    new_expiry = request.form["expirydate"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Pantry SET name = ?, expirydate = ? WHERE id = ?", 
                   (new_name, new_expiry, item_id))
    conn.commit()
    conn.close()
    return redirect(url_for("pantry"))

# to delete a pantry item from the database
@app.route("/delete/<int:item_id>", methods=["POST"])
def delete(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Pantry WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("pantry"))


if __name__ == "__main__":
    app.run(debug=True)