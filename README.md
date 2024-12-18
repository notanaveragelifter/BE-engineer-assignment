### README for BE Engineer Assignment

# FastAPI Scraping Tool

This project is a web scraping tool developed using the **FastAPI** framework that scrapes product details (name, price, and image) from a specified e-commerce website (`https://dentalstall.com/shop/`). The tool stores the scraped data as a JSON file and supports proxy configuration for scraping. The project also includes simple authentication using a static token, retry mechanisms for failed requests, and a Redis-based caching mechanism to ensure data integrity and avoid redundant updates.

## Project Structure

```plaintext
.
├── app.py                # Main FastAPI application
├── images/               # Directory to store downloaded images
├── scraped_data/         # Directory to store scraped JSON data
├── requirements.txt      # Project dependencies
└── README.md             # This README file
```

## Features

- **Web Scraping**: Scrapes product details (name, price, image URL) from the provided e-commerce website.
- **Configurable Settings**:
  - `pages`: Limit the number of pages to scrape.
  - `proxy`: Provide a proxy server for the scraper.
- **Redis Caching**: Uses Redis to store scraped product prices to avoid redundant updates when the price hasn't changed.
- **Retry Mechanism**: Includes a retry mechanism that attempts to scrape the page up to 3 times if it fails.
- **Authentication**: Basic authentication using a static token to secure the endpoints.
- **Image Download**: Downloads and stores product images locally.
- **JSON Data**: Saves the scraped data in a JSON file with details like product title, price, and image path.
- **Notification**: Prints a simple notification in the console when scraping is complete, specifying how many products were scraped and updated.

## Installation

### Prerequisites

- **Python** 3.8+
- **Redis** (Installed locally or use a cloud Redis service)
- Install **FastAPI** and **Uvicorn** for running the application
- Install **requests**, **beautifulsoup4**, **redis** for scraping and caching

### Step 1: Clone the Repository

```bash
git clone https://github.com/notanaveragelifter/BE-engineer-assignment.git
cd BE-engineer-assignment
```

### Step 2: Install Dependencies

Create a virtual environment (optional) and install the required dependencies:

```bash
pip install -r requirements.txt
```

### Step 3: Start Redis Server

Ensure that you have Redis installed and running on your local machine. If you haven't installed it yet, follow the [Redis installation guide](https://redis.io/docs/getting-started/).

To start the Redis server:

```bash
redis-server
```

### Step 4: Run the FastAPI Application

You can run the FastAPI application using **Uvicorn**:

```bash
uvicorn app:app --reload
```

The application will be accessible at `http://127.0.0.1:8000`.

## API Endpoints

### 1. **Start Scraping**

**POST** `/scrape/`

Start scraping the product data from the website.

**Parameters**:

- `pages` (Optional): Number of pages to scrape. Default is `5`.
- `max_products` (Optional): Maximum number of products to scrape. Default is `10`.
- `token` (Required): Static token for authentication (e.g., `"static-token"`).
- `proxy` (Required): Proxy dictionary, e.g., `{
  "proxy": {
    "http": "http://your_proxy_address:port",
    "https": "https://your_proxy_address:port"
  }
}
`.

**Response**:
- `"message"`: A message indicating how many products were successfully scraped.

**Example**:

```json
{
  "pages": 3,
  "max_products": 5,
  "token": "static-token",
  "proxy": {"http": "http://your_proxy_here"}
}
```

**Response**:

```json
{
  "message": "Successfully scraped 5 products!"
}
```

### 2. **Health Check**

**GET** `/`

Checks if the scraping service is running.

**Response**:

```json
{
  "message": "Scraping service is running!"
}
```

## Caching with Redis

Redis is used to cache the product prices during the scraping process. If a product's price hasn't changed since the last scrape, the tool will skip saving the new data for that product.

- Product price data is stored in Redis with a key format like `product:{title}`, where `{title}` is the product title.
- If the price has changed, the product details are updated, and the new price is stored in Redis.

## Directory Structure

### `scraped_data/`
- Stores the scraped product data in a JSON file (`products.json`).

### `images/`
- Stores the product images that are downloaded during the scraping process. The image is named after the product title (with spaces replaced by underscores).

### Sample Scraped Data (products.json)

```json
[
  {
    "product_title": "Product Name 1",
    "product_price": 299,
    "path_to_image": "images/product_name_1.jpg"
  },
  {
    "product_title": "Product Name 2",
    "product_price": 499,
    "path_to_image": "images/product_name_2.jpg"
  }
]
```

## Example Use Cases

1. **Scrape 5 Pages with a Proxy**:

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/scrape/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "pages": 5,
  "max_products": 10,
  "token": "static-token",
  "proxy": {"http": "http://your_proxy_here"}
}'
```

2. **Health Check**:

```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/'
```

**Response**:

```json
{
  "message": "Scraping service is running!"
}
```

## Notes

- Make sure you replace `proxy` with a valid proxy URL for scraping.
- The `STATIC_TOKEN` should be passed in the `token` field of the request body.
- The application relies on Redis for caching, so ensure that Redis is running on `localhost` by default.

## Troubleshooting

- **Redis Connection Issues**: Ensure Redis is installed and running. Check if you can connect to Redis using the `redis-cli` tool.
- **Proxy Errors**: Ensure the proxy is reachable and correctly configured.
- **Authentication Errors**: Ensure you're using the correct static token (`"static-token"`) for authentication.


