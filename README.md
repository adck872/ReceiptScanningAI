# ProjectReceiptScan

A flask based web app that uses OCR and NLP techniques to extract food items from a receipt to aumtomatically update your pantry by matching the extracted items to a local database which contains food items with its expiry dates, for pantry management

## Features

1. Upload a receipt image to automatically update pantry
2. View and edit Pantry Contents
3. Notifications in app for items expiring soon

## Requirements

Any IDE that can run python

## Prerequisites

Python
A browser and a working internet connection

## Installation

1. Set up a virtual environment (recommended) in Windows PowerShell:

```
python -m venv env
.\env\Scripts\Activate.ps1

```

if policy error occurs:

```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. Install required packages:

```
pip install -r requirements.txt

```

## Usage

- must be in the interface directory to run test.py and app.py
  Run the script with the following command:

```
cd interface
flask run --host=0.0.0.0

# there will be 2 addresses: first will be the web version, second is the ip address you put in your mobile browser to use as a mobile app

to test receipt images only use the image light2.jpg found in receipt folder
```

## interface folder

interface/

├── static/ # Static files (CSS, images)
│ ├── images/ # Images used in flask web app
│ ├── index.css # CSS for index page
│ └── pantry.css # CSS for pantry page
├── templates/ # HTML templates
│ ├── index.html # uploading receipts, viewing total pantry contents , and viewing notifications
│ └── pantry.html # Pantry page to edit or delete food items
├── -- SQLite.sql # sql script to add or delete database items
├── app.py # Main Flask app
├── food_db.db # SQLite database file
├── init_db.py # Script to initialize the database
└── test.py # Test to see database contents

## Sprints folder

- sprint1.ipynb tests for basic ocr text extraction
- sprint2.ipynb preprocessing images
- sprint2regex.ipynb regex patterns
- sprint3.ipynb fuzzy matching food names

## Contact

Any questions of feedback feel free to reach out to me:
fatima.ahmed.3@city.ac.uk
