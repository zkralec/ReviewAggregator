import requests
import csv

from bs4 import BeautifulSoup
from urllib.parse import urljoin

# GET request
url = 'https://www.trustpilot.com/review/www.amazon.com'

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

response = requests.get(url, headers=headers)

# Parsing the HTML
soup = BeautifulSoup(response.text, 'html.parser')

# Writing review, author, and rating to CSV
review_file = open('reviews.csv', mode='w', newline='', encoding='utf-8')
writer = csv.writer(review_file)
writer.writerow(['Author', 'Rating', 'Review'])

# Initializing temp href
href = 'temp'

while href is not None:

    numReviewsOnPage = 0

    # Get review block
    review_block = soup.find_all('div', class_='styles_cardWrapper__g8amG styles_show__Z8n7u') # Could be too broad

    # print(review_block)

    # Getting each review, author, and rating in block
    for i in review_block:
        numReviewsOnPage += 1
        author = i.find('span', class_='typography_heading-xs__osRhC typography_appearance-default__t8iAq').get_text()
        rating_tag = i.find('div', class_='star-rating_starRating__sdbkn star-rating_medium__Oj7C9').find('img')
        rating = rating_tag.get('alt') if rating_tag else 'N/A'
        review_tag = i.find('p', class_='typography_body-l__v5JLj typography_appearance-default__t8iAq')
        review = review_tag.get_text() if review_tag else 'N/A'

        writer.writerow([author, rating, review])

    # Getting the href for the next page
    href = soup.find('a', rel='next')

    # Edge case for certain pages
    if not href:
        href = soup.find('a', attrs={'aria-label': 'Next page'})

    # Gets the new link and page
    if href and href.get('href'):
        next_page_url = urljoin(url, href['href'])
        print("Now on:", next_page_url)
        response = requests.get(next_page_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        print("Reviews Scraped from page: " + str(numReviewsOnPage))
    else:
        href = None

# Closing the CSV file
review_file.close()
print("DONE: Check the 'reviews.csv' file for all scraped reviews")
