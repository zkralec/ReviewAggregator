import requests
import csv
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Method for calculating average review
def avg_review(rating_list):

    # Edge case for no reviews
    if not rating_list:
        print("\nNo ratings to average.\n")
        return
    else:
        return round(sum(rating_list) / len(rating_list), 2)

# Method for safely getting text
def safe_text(node):
    return node.get_text(strip=True) if node else "N/A"

# Regex for pulling the number out of alt="Rated X out of 5"
RATING_ALT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*out\s*of\s*5", re.I)

# Prompt user for the company they want to review
web_name = input('\n\nPlease enter the weblink of the company you want reviews for.\nNote, quick back to back requests can cause issues. \n\nEx. amazon.com \n    nike.com \n    temu.com \n\nYour selection: ')
web_name = web_name.strip().lstrip("/")

# GET request
url = 'https://www.trustpilot.com/review/' + web_name
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# Ensure url works
try:
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 404:
        print(f'\n❌ No Trustpilot page found for: {web_name}\n')
        exit()
    elif response.status_code != 200:
        print(f'\n⚠️ Failed to load page (status code {response.status_code}). Try again later.\n')
        exit()
except requests.exceptions.MissingSchema:
    print('\n❌ You entered an invalid URL format. Type something like "nike.com".\n')
    exit()
except requests.exceptions.RequestException as e:
    print(f'\n❌ A network error occurred: {e}\n')
    exit()

# Prompt user for number of reviews they want
max_reviews = input("\nHow many reviews would you like to scrape?\n\n")

# Limit user options to be reasonable
try:
    if int(max_reviews) >= 50000:
        print('\n❌ Please enter a valid number less than 50000.\n')
        exit()
    elif int(max_reviews) > 0:
        max_reviews = int(max_reviews)
    else:
        print('\n❌ Please enter a valid number greater than 0.\n')
        exit()
except ValueError:
    print('\n❌ Please enter a valid number greater than 0.\n')
    exit()

# Parsing the HTML
soup = BeautifulSoup(response.text, 'html.parser')

# Writing review, author, and rating to CSV
review_file = open('reviews.csv', mode='w', newline='', encoding='utf-8')
writer = csv.writer(review_file)
writer.writerow(['Author', 'Rating', 'Review'])

# Initializing counter for reviews scraped
num_reviews = 0

# Initializing list for all ratings
rating_list = []

while True:

    # Each review is inside an article with this attribute
    review_cards = soup.select('article[data-service-review-card-paper="true"]')

    # Fallback in case the above changes
    if not review_cards:
        review_cards = soup.find_all('div', class_=re.compile(r'^styles_cardWrapper__'))

    for card in review_cards:

        # End program if number of reviews satisfies user selection
        if num_reviews >= max_reviews:
            review_file.close()
            print(f'\nThe average rating for {web_name} was {avg_review(rating_list)}/5.\n')
            print('✅ DONE: Check the "reviews.csv" file for all scraped reviews.\n')
            exit()

        # Getting author
        author = "N/A"
        author_label = card.select_one('aside[aria-label^="Info for"]')
        if author_label:
            author = safe_text(author_label)
        if author == "N/A":
            author_link = card.find('a', href=re.compile(r'/users/'))
            if author_link:
                author = safe_text(author_link)
        if author == "N/A":
            author_span = card.find('span', class_=re.compile(r'^typography_heading-xs__'))
            if author_span:
                author = safe_text(author_span)

        # Getting rating
        rating_value = None
        rating_img = card.select_one('img[alt*="out of 5" i]')
        if rating_img and rating_img.has_attr('alt'):
            m = RATING_ALT_RE.search(rating_img['alt'])
            if m:
                try:
                    rating_value = float(m.group(1))
                except ValueError:
                    rating_value = None

        # Getting review text
        review = "N/A"
        review_node = card.select_one('[class*="reviewText"]')
        if review_node:
            review = safe_text(review_node)
        if review == "N/A":
            ps = card.find_all('p')
            if ps:
                review = max((p.get_text(strip=True) for p in ps), key=len, default="N/A")

        # Adding each rating to the list
        if rating_value is not None:
            rating_list.append(rating_value)

        # Write to file and increase reviews found
        writer.writerow([author, rating_value if rating_value is not None else "N/A", review])
        num_reviews += 1

    # Getting the href for the next page
    href = soup.find('a', rel='next')
    if not href:
        href = soup.find('a', attrs={'aria-label': 'Next page'})

    # Gets the new link and page
    if href and href.get('href'):
        next_page_url = urljoin(url, href['href'])
        response = requests.get(next_page_url, headers=headers)
        if response.status_code != 200:
            break
        soup = BeautifulSoup(response.text, 'html.parser')
        time.sleep(0.8)
    else:
        break

# Closing the CSV file and final print statements
review_file.close()
print(f'\nThe average rating for {web_name} was {avg_review(rating_list)}/5.\n')
print('⚠️ DONE: There are less reviews than what you requested. Scraped all reviews instead. Check the "reviews.csv" file for all scraped reviews.\n')
