from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bs4 import BeautifulSoup
import requests
import json
import os
import time
import redis  # Redis library to interact with Redis DB

# Initialize FastAPI
app = FastAPI()

# Directory paths for saving data
SCRAPED_DATA_DIR = 'scraped_data'
IMAGES_DIR = 'images'

# Create directories if they don't exist
if not os.path.exists(SCRAPED_DATA_DIR):
    os.makedirs(SCRAPED_DATA_DIR)
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# Redis Configuration (default localhost and port 6379)
r = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

# Define a static token for authentication
STATIC_TOKEN = "static-token"

# Dependency to verify token
def verify_token(authorization: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    if authorization.credentials != STATIC_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

# Scraper class to always use a proxy
class Scraper:
    def __init__(self, url: str, redis_client, proxy: dict, max_retries: int = 3, retry_delay: int = 3):
        self.url = url
        self.redis_client = redis_client
        self.proxy = proxy  # Proxy is now mandatory
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    # Retry mechanism with mandatory proxy
    def retry_request(self, url):
        for attempt in range(self.max_retries):
            try:
                # Always pass the proxy to requests.get
                response = requests.get(url, proxies=self.proxy)
                if response.status_code == 200:
                    return response
                else:
                    print(f"Error {response.status_code}, retrying...")
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}, retrying...")
            time.sleep(self.retry_delay)
        return None

    # Placeholder for notification system
    def send_notification(self, message: str):
        print(f"NOTIFICATION: {message}")

    # Web scraping logic with Redis caching
    def scrape_data(self, pages: int = 5, max_products: int = 10):
        all_products = []
        scraped_count = 0  # Track the number of products scraped

        for page in range(1, pages + 1):
            page_url = f"{self.url}page/{page}/"
            print(f"Scraping page {page_url}")

            response = self.retry_request(page_url)
            if not response:
                raise HTTPException(status_code=500, detail="Failed to retrieve the page after multiple retries")

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all product items (adjusted tag and class for product list)
            products = soup.find_all('li', class_='product')

            for product in products:
                if scraped_count >= max_products:  # Stop once we reach the max number of products
                    break

                # Correct the tag and class names for title, price, and image
                title_tag = product.find('h2', class_='woo-loop-product__title')
                price_tag = product.find('span', class_='woocommerce-Price-amount amount')
                img_tag = product.find('img', class_='mf-product-thumbnail')

                # Extract title, price, and image URL safely
                title = title_tag.text.strip() if title_tag else "No title found"
                price = price_tag.text.strip() if price_tag else "No price found"
                img_url = img_tag['src'] if img_tag else ""

                if price:
                    # Remove unwanted symbols (including ₹ symbol or any characters before the price number)
                    price = ''.join(filter(str.isdigit, price))  # Keep only digits
                    
                    # Ensure the price has 2 decimal places
                    if len(price) > 2:
                        price = f"{price[:-2]}.{price[-2:]}"  # Move the last two digits to decimal places
                    else:
                        price = f"{price}.00" 

                # Check if product already exists in Redis and if the price has changed
                existing_price = self.redis_client.get(f"product:{title}")

                if existing_price and existing_price == price:
                    print(f"Price for '{title}' has not changed, skipping update.")
                    continue  # Skip if the price has not changed

                # Download the image if a valid URL is found
                img_path = f"{IMAGES_DIR}/{title.replace('/', '_').replace(' ', '_')}.jpg"
                try:
                    if img_url:
                        img_data = requests.get(img_url, proxies=self.proxy).content
                        with open(img_path, 'wb') as img_file:
                            img_file.write(img_data)
                except Exception as e:
                    print(f"Failed to download image for {title}: {e}")

                # Update product data in Redis (set product title and price)
                self.redis_client.set(f"product:{title}", price)

                # Append product details to the list
                all_products.append({
                    "product_title": title,
                    "product_price": price,
                    "path_to_image": img_path
                })
                scraped_count += 1  # Increment the product count

            # If we've scraped enough products, break the outer loop
            if scraped_count >= max_products:
                break

        # Save the scraped data to a JSON file
        json_file_path = os.path.join(SCRAPED_DATA_DIR, 'products.json')
        with open(json_file_path, 'w') as f:
            json.dump(all_products, f, indent=4)

        # Send a notification once the scraping is finished
        self.send_notification(f"Scraping session completed. {scraped_count} products scraped and updated in the database.")

        return scraped_count  # Return the actual number of scraped products

# Endpoint to start scraping with proxy support
@app.post("/scrape/") 
async def start_scraping(pages: int = 5, max_products: int = 10, token: str = Depends(verify_token), proxy: dict = None):
    # Ensure proxy is always provided
    if proxy is None:
        raise HTTPException(status_code=400, detail="Proxy is required.")
    
    # Pass proxy to Scraper
    scraper = Scraper(url="https://dentalstall.com/shop/", redis_client=r, proxy=proxy)
    try:
        scraped_count = scraper.scrape_data(pages=pages, max_products=max_products)
        if scraped_count == max_products:
            return {"message": f"Successfully scraped {scraped_count} products!"}
        else:
            return {"message": f"Scraped only {scraped_count} products (less than the requested {max_products})."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Scraping service is running!"}
