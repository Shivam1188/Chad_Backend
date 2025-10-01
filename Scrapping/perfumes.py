import asyncio
from playwright.async_api import async_playwright
import json
import os
import pickle
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request


# The Google Sheets API requires a token file for authentication
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '1GIwoCBmFeqvbowlJpvFz-c8Wkzz_FnA0E_N_qAc_PBY' 

# Authenticate Google Sheets API using a service account
def authenticate_sheets():
    creds = None
    # Load the service account credentials from the JSON file
    creds = Credentials.from_service_account_file(
        'credentials.json', scopes=SCOPES)

    # Build the Google Sheets API client
    service = build('sheets', 'v4', credentials=creds)
    return service


# Write data to Google Sheets
def write_to_sheets(data):
    service = authenticate_sheets()
    sheet = service.spreadsheets()

    # Prepare data for writing into the sheet (Convert the list of dictionaries to rows)
    rows = [['Product URL', 'Title', 'Image URL', 'Review Author', 'Review Date', 'Review Text']]  # Headers
    for product in data:
        for review in product['reviews']:
            rows.append([
                product['url'],
                product['title'],
                product['image'],
                review['author'],
                review['date'],
                review['review_text']
            ])

    # Insert the rows into the Google Sheet
    try:
        response = sheet.values().update(
            spreadsheetId=SHEET_ID,
            range="Sheet1!A1",  # Change to your desired sheet and range
            valueInputOption="RAW",
            body={"values": rows}
        ).execute()
        print(f"Data written to sheet: {response}")
    except HttpError as err:
        print(f"An error occurred: {err}")


async def slow_scroll(page):
    """Slowly scroll down the page as if a user is scrolling with the mouse."""
    scroll_position = 0
    while True:
        # Scroll 100px at a time
        scroll_position += 800
        await page.evaluate(f"window.scrollTo(0, {scroll_position});")
        await asyncio.sleep(0.5)  # Allow content to load (you can adjust the sleep time)

        # Check if we've reached the end of the page
        new_scroll_position = await page.evaluate("document.body.scrollHeight")
        if scroll_position >= new_scroll_position:
            break

async def scrape_reviews(page):
    """Scrape reviews once content is loaded."""
    try:
        # Wait for the reviews section to be loaded
        await page.wait_for_selector('.cell.small-10.flex-container.flex-dir-column', timeout=60000)  # Wait for 60 seconds max

        # Scrape reviews data
        reviews = []
        review_elements = await page.query_selector_all('.cell.small-10.flex-container.flex-dir-column')
        
        if not review_elements:
            print("No reviews found.")
            return reviews

        for review_element in review_elements:
            # Extract review text
            review_body_element = await review_element.query_selector('[itemprop="reviewBody"]')
            review_body = await review_body_element.inner_text() if review_body_element else "No review text"

            # Extract author name
            author_element = await review_element.query_selector('.idLinkify a')
            author_name = await author_element.inner_text() if author_element else "Unknown"

            # Extract review date
            date_element = await review_element.query_selector('[itemprop="datePublished"]')
            review_date = await date_element.inner_text() if date_element else "No date"

            reviews.append({
                'author': author_name,
                'review_text': review_body,
                'date': review_date
            })
    
    except Exception as e:
        print(f"Error during review scraping: {e}")
        reviews = []
    
    return reviews


async def scrape_product(browser, url):
    page = await browser.new_page()
    try:
        await page.goto(url)
        await slow_scroll(page)

        # Scrape title
        title_locator = page.locator('h1[itemprop="name"]')
        title = await title_locator.inner_text() if await title_locator.count() > 0 else "N/A"

        # Scrape image
        image_locator = page.locator('picture img[itemprop="image"]')
        image = await image_locator.get_attribute('src') if await image_locator.count() > 0 else "N/A"

        # Scrape reviews
        reviews = await scrape_reviews(page)

        if reviews:
            # Print the reviews
            for review in reviews:
                print(f"Author: {review['author']}")
                print(f"Review Date: {review['date']}")
                print(f"Review Text: {review['review_text']}")
                print('-' * 50)
        else:
            print("No reviews found or failed to scrape.")

        print(f"Scraped: {title.strip()} with {len(reviews)} reviews")
        return {
            "url": url,
            "title": title.strip(),
            "image": f"https://www.fragrantica.com{image}" if image.startswith('/') and image else image,
            "reviews": reviews
        }
    except Exception as e:
        print(f"Error scraping product {url}: {e}")
        return None
    finally:
        await page.close()


async def get_all_product_links(page):
    links = []
    while True:
        await page.wait_for_selector('div.prefumeHbox', timeout=20000)
        previous_height = None
        while True:
            current_height = await page.evaluate("document.body.scrollHeight")
            if previous_height == current_height:
                break
            previous_height = current_height
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        
        link_elements = await page.locator('div.prefumeHbox h3 a').all()
        for el in link_elements:
            href = await el.get_attribute('href')
            if href and href.startswith('/perfume/MiN-NEW-YORK/'):
                links.append(f"https://www.fragrantica.com{href}")
        
        next_btn = page.locator('ul.pagination li.next a')
        if await next_btn.count() == 0:
            break
        next_href = await next_btn.get_attribute('href')
        if not next_href:
            break
        await page.goto(f"https://www.fragrantica.com{next_href}", wait_until="networkidle")
        await asyncio.sleep(2)
    
    return links


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
        await page.goto("https://www.fragrantica.com/designers/MiN-NEW-YORK.html", wait_until="load")
        await asyncio.sleep(5)

        links = await get_all_product_links(page)
        print(f"Found {len(links)} product links.")
        await page.close()

        scraped_data = []
        for link in links:
            try:
                product_data = await scrape_product(browser, link)
                if product_data:
                    scraped_data.append(product_data)
                await asyncio.sleep(2)  # Increased pause to avoid rate limiting
            except Exception as e:
                print(f"Error scraping {link}: {e}")

        # Write data to Google Sheets
        write_to_sheets(scraped_data)

        print(f"Scraped {len(scraped_data)} perfumes. Data written to Google Sheets.")
        await browser.close()

asyncio.run(main())
