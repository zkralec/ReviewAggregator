import requests
import csv

from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Prompt user for the company they want to review
web_name = input('\n\nPlease enter weblink of the company you want reviews for.\nNote, quick back to back requests can cause issues. \n\nEx. amazon.com \n    nike.com \n    temu.com \n\nYour selection: ')

# GET request
url = 'https://www.trustpilot.com/review/' + web_name
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

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
max_reviews = input("\nHow many reviews would you like to recieve?\n\n")

try:
    max_reviews = int(max_reviews)
except ValueError:
    print("\n❌ Please enter a valid whole number.\n")
    exit()

# Parsing the HTML
soup = BeautifulSoup(response.text, 'html.parser')

# Writing review, author, and rating to CSV
review_file = open('reviews.csv', mode='w', newline='', encoding='utf-8')
writer = csv.writer(review_file)
writer.writerow(['Author', 'Rating', 'Review'])

# Initializing temp href
href = 'temp'

# Initializing counter for reviews scraped
num_reviews = 0

while href is not None:

    # Get review block
    review_block = soup.find_all('div', class_='styles_cardWrapper__g8amG styles_show__Z8n7u')

    # Getting each review, author, and rating in block
    for i in review_block:

        # End program if number of reviews satisfies user selection
        if num_reviews >= max_reviews:
            review_file.close()
            print('✅ DONE: Check the "reviews.csv" file for all scraped reviews.')
            exit()

        author = i.find('span', class_='typography_heading-xs__osRhC typography_appearance-default__t8iAq').get_text()
        rating_tag = i.find('div', class_='star-rating_starRating__sdbkn star-rating_medium__Oj7C9').find('img')
        rating = rating_tag.get('alt') if rating_tag else 'N/A'
        review_tag = i.find('p', class_='typography_body-l__v5JLj typography_appearance-default__t8iAq')
        review = review_tag.get_text() if review_tag else 'N/A'

        writer.writerow([author, rating, review])
        num_reviews += 1

    # Getting the href for the next page
    href = soup.find('a', rel='next')

    # Edge case for certain pages
    if not href:
        href = soup.find('a', attrs={'aria-label': 'Next page'})

    # Gets the new link and page
    if href and href.get('href'):
        next_page_url = urljoin(url, href['href'])
        print('Scraping: ' + next_page_url)
        response = requests.get(next_page_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
    else:
        href = None

# Closing the CSV file
review_file.close()
print('⚠️ DONE: There are less reviews than what you requested. Scraped all reviews instead. Check the "reviews.csv" file for all scraped reviews')
