import json
from time import sleep

import requests
from selenium import webdriver

from product import Product

exhange_rate_GBP_URL = 'https://api.exchangerate-api.com/v4/latest/GBP'

amazon_URL = "https://www.amazon.co.uk/"


def get_exchange_rate():
    response = requests.get(exhange_rate_GBP_URL)
    return response.json()['rates']['SEK']


# Setup browser
options = webdriver.FirefoxOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--headless')
driver = webdriver.Firefox(options=options)

search_term = str(input("Search: "))
gbp_to_sek = get_exchange_rate()

driver.get(amazon_URL)
search_element = driver.find_element_by_css_selector('#twotabsearchtextbox')
search_element.send_keys(search_term)
search_element.submit()

products = []

page = 1


def convert_string_price_to_float(price_text):
    price = price_text.split("£")[1]
    try:
        price = price.split("\n")[0] + "." + price.split("\n")[1]
    except:
        Exception()
    try:
        price = price.split(",")[0] + price.split(",")[1]
    except:
        Exception()

    return round(float(price) * gbp_to_sek)


while True:

    # Sleep 0.5 seconds to not put to much stress on the website
    sleep(0.5)
    if page != 1:
        try:
            driver.get(driver.current_url + '&page=' + str(page))
        except:
            raise Exception("Could not change page")

    # Loop through every item in page x.
    for i in driver.find_elements_by_css_selector('.s-result-list'):

        counter = 0
        # For every element in page x
        for element in i.find_elements_by_css_selector('.s-result-item'):
            should_add = True
            name = ""
            price = ""
            prev_price = ""
            link = ""
            try:
                name = i.find_elements_by_tag_name('h2')[counter].text
                price = convert_string_price_to_float(element.find_element_by_class_name('a-price').text)
                link = i.find_elements_by_xpath('//h2/a')[counter].get_attribute("href")
                try:
                    prev_price = convert_string_price_to_float(element.find_element_by_class_name('a-text-price').text)
                except:
                    Exception()
                    prev_price = price
            except:
                should_add = False

            product = Product(name, price, prev_price, link)
            if should_add:
                products.append(product)
            counter += 1

    page += 1
    if page >= 3:
        break

biggest_discount = 0.0
lowest_price = 0.0
discount = 0.0
cheapest_product = Product("", "", "", "")
best_deal_product = Product("", "", "", "")
search_terms = search_term.split(" ")

run = 0

for product in products:
    correct_product = True
    for word in search_terms:
        if word.lower() not in product.name.lower():
            correct_product = False

    if correct_product:
        if run == 0:
            lowest_price = product.price
            cheapest_product = product
            run = 1
        elif product.price < lowest_price:
            lowest_price = product.price
            cheapest_product = product
        else:
            discount = product.prev_price - product.price
        if discount > biggest_discount:
            biggest_discount = discount
            best_deal_product = product

with open('products.json', 'w') as json_file:
    data = {"Products": []}
    for prod in products:
        data["Products"].append(prod.serialize())

    json.dump(data, json_file, sort_keys=True, indent=4)

print(json.dumps(cheapest_product.serialize(), sort_keys=True, indent=4))
print(json.dumps(best_deal_product.serialize(), sort_keys=True, indent=4))

driver = webdriver.Firefox()
driver.get(best_deal_product.link)
