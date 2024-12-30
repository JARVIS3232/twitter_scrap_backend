from flask import Flask, jsonify, request
from flask_cors import CORS
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import uuid
from pymongo import MongoClient
from datetime import datetime
import socket


USERNAME = "TestScrap37394"
EMAIL= "yehogod688@gholar.com" # Sometimes Twitter ask for email as well 
PASSWORD = "Test@123"

MONGO_URI="mongodb+srv://root:123@cluster0.rt3dn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

DB_NAME = "twitter_data" 
COLLECTION_NAME = "trends"

app = Flask(__name__)
CORS(app)

def get_ip_address():
    return socket.gethostbyname(socket.gethostname())

def login_to_twitter(driver):
    driver.get("https://x.com/i/flow/login")
    time.sleep(3)

    # I am using for loop to enter single character at a time ,So that it looks real 

    username_field = driver.find_element(By.NAME, "text")
    for char in USERNAME: 
        username_field.send_keys(char)
        time.sleep(0.05)  
    username_field.send_keys(Keys.RETURN)
    time.sleep(2)
    
    # Email is optional
    try:
        email_field = driver.find_element(By.NAME, "text")
        if email_field:
            for char in EMAIL:  
                email_field.send_keys(char)
                time.sleep(0.05)
            email_field.send_keys(Keys.RETURN)
            time.sleep(3)
    except Exception as e:
        print("Email field not required, skipping step.")

    password_field = driver.find_element(By.NAME, "password")
    for char in PASSWORD:  
        password_field.send_keys(char)
        time.sleep(0.05) 
    password_field.send_keys(Keys.RETURN)
    time.sleep(3)

def scrape_whats_happening(driver):
    try:
        driver.get("https://x.com/home")
        time.sleep(6)
        whats_section = driver.find_element(By.XPATH, 
            '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div')
        html_content = whats_section.get_attribute("outerHTML")
        soup = BeautifulSoup(html_content, "html.parser")
        span_elements = soup.find_all("span")
        unique_trends =set()
        trends = []
        for span in span_elements:
            text = span.get_text(strip=True)
            if text and not text.isdigit() and "posts" not in text.lower() and "Trending" not in text:
                if text not in trends:
                   unique_trends.add(text)
                   trends.append(text)
        print("Trending Topics Extracted: ", trends)
        return trends[1:6]
    except Exception as e:
         print("Error in scraping data: ", e)

def save_to_mongodb(data):
    try:
       client = MongoClient(MONGO_URI)
       db = client[DB_NAME]
       collection = db[COLLECTION_NAME]
       collection.insert_one(data)
       print("Data successfully inserted into MongoDB.")
    except Exception as e:
       print("Error saving data in database")   
    finally:   
       client.close()

@app.route('/run-script', methods=['POST'])
def run_script():
    try:
        PROXY="45.32.86.6:31280"
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  
        # options.add_argument('--proxy-server=%s' % PROXY)
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        login_to_twitter(driver)
        trends = scrape_whats_happening(driver)
        if not trends:
           return jsonify({"message": "Failed to fetch trends."}), 500
        data = {
            "unique_id": str(uuid.uuid4()),
            "trends": trends,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip_address": get_ip_address()
        }
        save_to_mongodb(data)
        data["_id"] = str(data.get("_id"))
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"message": "Unknown error occured !"}), 500
    finally:
        driver.quit()


if __name__ == "__main__":
   app.run(debug=True)
