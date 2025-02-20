import time
import logging
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup 

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Set up Chrome options
options = webdriver.ChromeOptions()
options.add_argument("user-data-dir=C:/Users/KAREN/AppData/Local/Google/Chrome/User Data")
options.add_argument("profile-directory=Profile 2")  # Change this if needed
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_experimental_option("detach", True)  # Keep Chrome open

# Start WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Open Amazon Order History page
amazon_orders_url = "https://www.amazon.in/gp/css/order-history?ref_=nav_AccountFlyout_orders"
driver.get(amazon_orders_url)
time.sleep(5)  # Wait for the page to load

logging.info("✅ Amazon order history page loaded.")

# List of years to scrape
years = ["2024", "2023", "2022", "2021","2020","2019","2018","2017"]
all_orders = []

# Loop through each year and extract orders
for year in years:
    try:
        # Open the filter dropdown
        dropdown = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "a-autoid-1-announce")))
        dropdown.click()
        time.sleep(2)

        # Select the year from dropdown
        option_year = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{year}')]"))
        )
        option_year.click()
        time.sleep(5)

        logging.info(f"✅ Successfully changed filter to {year}.")

    except Exception as e:
        logging.warning(f"⚠️ Could not select {year} filter: {e}")
        continue  # Skip this year and move to the next

    # Extract orders for the selected year
    while True:
        # ✅ Use BeautifulSoup to parse the page source
        soup = BeautifulSoup(driver.page_source, "html.parser")

        order_elements = soup.select("div.order-card.js-order-card")  # Select all order blocks

        for order in order_elements:
            try:
                # ✅ Extract Order Number
                order_number_element = order.find("span", text=re.compile("Order #"))
                order_number = order_number_element.find_next_sibling("span").text.strip() if order_number_element else "N/A"

                # ✅ Extract Order Date Correctly
                order_date_element = order.select_one("div.a-column.a-span3 div.a-row span.a-size-base")
                order_date = order_date_element.text.strip() if order_date_element else "Unknown Date"

                # ✅ Extract Order Total Correctly
                order_total_element = order.select_one("div.a-column.a-span2 div.a-row span.a-size-base")
                order_total = order_total_element.text.strip() if order_total_element else "N/A"


                # ✅ Extract Product Title
                product_title_element = order.select_one("div.yohtmlc-product-title")
                product_title = product_title_element.text.strip() if product_title_element else "No Product Found"

                # ✅ Fix Encoding Issues
                product_title = product_title.encode("utf-8", "ignore").decode("utf-8")

                # Store the order details
                all_orders.append({
                    "Year": year,
                    "Order Number": order_number,
                    "Date": order_date,
                    "Total Price": order_total,
                    "Product": product_title
                })

            except Exception as e:
                logging.warning(f"⚠️ Skipping an order due to error: {e}")

        logging.info(f"📌 Extracted {len(all_orders)} orders so far for {year}.")

        # Try to go to the next page
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Next') or contains(text(), 'Next Page')]"))
            )
            next_button.click()
            time.sleep(5)
        except:
            logging.info(f"✅ No more pages for {year}. Moving to the next year.")
            break  # Exit loop when no more pages

# Save orders to CSV
df = pd.DataFrame(all_orders)
df.to_csv("dataset.csv", index=False, encoding="utf-8-sig")  # ✅ Added encoding for special characters
logging.info("✅ Saved all orders to dataset.csv")

input("Press Enter to close the browser...")
driver.quit()
