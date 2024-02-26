from playwright.async_api import async_playwright
import random
from web_agent import WebAgent
import asyncio

async def run() -> None:
    async with async_playwright() as playwright:
        item_name = "Popcorners - Sea Salt - 3.0 oz"
        search_name = 'popcorner'
        
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        ## LOGGING IN
        await page.goto("https://shop.fls2u.com/login")
        await page.get_by_text("Accept All Cookies", exact=True).click()
        await page.get_by_label("Username / Email*").click()
        await page.get_by_label("Username / Email*").fill("jack@duffl.com")
        await page.get_by_label("Password*").click()
        await page.get_by_label("Password*").fill("dufflucsb2021")
        await page.get_by_label("login", exact=True).click()
        
        await page.wait_for_timeout(8000) # Wait for the page to load, adjust as needed

        ## Searching for the Item
        await page.wait_for_timeout(random.randint(2000, 5000)); 
        await page.get_by_placeholder("Search Product").click()
        await page.get_by_placeholder("Search Product").fill(search_name)
        await page.locator("#clear-search-icon svg").click()
        await page.wait_for_timeout(random.randint(5000, 8000))
        
        agent = WebAgent(page)
        
        await agent.process_page()
        await agent.chat(f"click the item that is {item_name}")
        await agent.chat("click the number box")
        await agent.chat("click 1")
        
        
        # ## Adding all item info into a map, mapped to the index of the items on this website
        # card_text_map = {}
        # card_titles = page.query_selector_all(".pro-list-title-mob")
        # for index, card_title in enumerate(card_titles):
        #     # Click on the card title to open the modal
        #     print('clicking on this card')
        #     card_title.click()

        #     # Wait for the modal to be visible if needed, assuming modal's text has a unique selector
        #     page.wait_for_selector(".product-title", state="visible")

        #     # Get the text from the modal
        #     print('getting the text')
        #     modal_text = page.inner_text(".product-title")
        #     print('documented the text: ' + modal_text)

        #     # Store the index and the text in the dict (using index as key since there's no unique id mentioned)
        #     card_text_map[index] = modal_text

        #     # Close the modal before moving on to the next card, adjust the selector as needed
        #     page.click('[aria-label="close"]')
        #     print("closed the card")
        #     page.wait_for_timeout(2000) # Wait for the modal to close, adjust as needed
        #     if index >= 5: ##currently only getting max 20 items
        #         break
            
        # # After the loop, you have your map filled
        # print('The item map has been filled. list of item names:')
        # print(card_text_map)
        
        # ## Find the index of the item on the website using GPT?
        # card_index = findItem(card_text_map, item_name)
        # print('now clicking on the' + str(card_index) + 'th card')
        
        # ## Click on the hopefully-correct item
        # click_card_by_index(page, card_index)
        await page.wait_for_timeout(50000)
        await context.close()
        await browser.close()
        
    # def findItem(dict, search_name):
    #     prompt = 'given a python dict, please return the key where the value of this key is "' + search_name + '" in the dict: ' + str(dict) + '. Since all my keys are integers, your reply must be an integer and nothing else'
    #     print('prompt: ' + prompt)
    #     card_index = ask_openai(prompt)
    #     print('gpt reply: ' + card_index) 
    #     return int(card_index)

def click_card_by_index(page, index):
    # Selector for all cards, assuming they can be selected with a common class or attribute
    cards_selector = ".pro-list-title-mob"

    # Wait for all the cards to be loaded and visible
    page.wait_for_selector(cards_selector)

    # Fetch all elements matching the cards selector
    cards = page.query_selector_all(cards_selector)

    if index < len(cards):
        # Click on the card at the given index
        cards[index].click()
        # You might need to add a wait here if the click triggers navigation or loads content
    else:
        print(f"Index {index} is out of range for the available cards.")

##testing gpt search given the array of items
# findItem({0: 'Mac-N-Cheese Cups Bold & Cheesy Flavored', 1: "Cheetos Mac'N Cheese Pasta With Flavored Sauce Flamin' Hot Flavor 2.11 Oz", 2: 'Mac-N-Cheese Cups Cheesy Jalapeno Flavored', 3: "Jack Link's Flavored Meat Stick Fritos Chili Cheese And Jalapeno Cheese 1.1 Oz", 4: "Jack Link's Cheese Stick + Meat Stick Jalapeno Cheese + Flamin Hot 1.1 Oz", 5: "Jack Link's Jerky Fritos Chili Cheese 0.92 Oz", 6: "Jack Link's Flavored Meat Stick Doritos Spicy Sweet Chilli 0.92 Oz", 7: "Jack Link's Beef Jerky Flamin' Hot Flavored 0.92 Oz", 8: "Jack Link's Steak Bites Original 1 3/4 Oz", 9: "Jack Link's Steak Bites Teriyaki 1.75 Oz", 10: "Jack Link's Jerky Fritos Chili Cheese Flavored 2.65 Oz"},
#          'hot flavored macn-n-cheese cups')


asyncio.run(run())
