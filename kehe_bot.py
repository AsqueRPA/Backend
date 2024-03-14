import asyncio
from web_agent import JoshyTrain
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
import csv
import re
import argparse

load_dotenv()

port = os.getenv("PORT")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)

        page = await browser.new_page()
        ## LOGGING IN
        await page.goto("https://connectretailer.kehe.com/")
        await page.wait_for_timeout(5000)
        await page.get_by_placeholder("e.g. contact@email.com").fill("batu@duffl.com")
        await page.click(".btn.btn-primary.btn-medium.login-button")
        await page.fill("#password", "dufflucla2020")
        await page.get_by_text("Log In", exact=True).click()

        await page.wait_for_timeout(8000)

        result_rows = []

        with open("kehe.csv", mode="r") as file:
            dict_reader = csv.DictReader(file)
            for row in dict_reader:
                search_terms = []
                row["updated_price"] = ""
                row["updated_upc"] = ""
                item_name = row["product_name"]
                # item_name = "Cheetos Crunchy - Cheddar Jalapeno - 3.25 oz"

                joshyTrain = JoshyTrain(page)
                search_instruction = """
            when you are searching for an item, try different search terms, for example: 
            if the full name is Cheetos Crunchy - Cheddar Jalapeno - 3.25 oz, you can try the following
            - Cheetos Crunchy Cheddar Jalapeno
            - Cheetos Crunchy
            - Cheddar Jalapeno
            - Cheetos
            - MAKE SURE TO ALSO TRY OTHER COMBINATION OF THE WORDS OR JUST THE BRAND NAME AS WELL
            """
                while True:
                    try:
                        response = await joshyTrain.chat(
                            f"""{search_instruction}, DO: INPUT different search terms into the search bar for {item_name}, you have already tried {search_terms}.

                            Just try once and then return the following JSON format: 
                            {{"searchTerm": "exact search term you put as the input", "itemsFound": "yes" or "no"}}

                            the above is your ONLY OPTION AFTER ATTEMPTING TO INPUT INTO THE SEARCH BAR, never output {{"searchTerm": "exact search term you put as the input", "itemsFound": "yes" or "no"}} if you haven't outputted {{"input": {{"select": "ID", "text": "exact search term you put as the input"}}}}

                            if you don't follow the above, then the program will not work.
                            """
                        )
                        data = joshyTrain.extract_json(response)
                        if data and "searchTerm" in data:
                            search_term = data["searchTerm"]
                            search_terms.append(search_term)
                            if str(data["itemsFound"]).lower() == "yes":
                                break
                    except Exception as e:
                        print(e)
                        continue
                response = await joshyTrain.chat(
                    f'tell me the name of the item in JSON format that is most similar to {item_name}, {{"name": "exact name of the item"}}'
                )
                data = joshyTrain.extract_json(response)
                if data and "name" in data:
                    name = data["name"]
                else:
                    name = item_name
                await joshyTrain.chat(
                    f"click the image for {name}  and don't do anything else"
                )
                number_of_packs = row["total_packs_ordered"]
                await joshyTrain.chat(
                    f"put {number_of_packs} for amount and click 'Add to Cart'. if it asks you for the order name, put 'test order' and click 'Add to Cart', otherwise do nothing."
                )

            cart_icon = await page.query_selector('img[src="www/images/cart.svg"]')
            await cart_icon.click()

            await page.screenshot(path="screenshot.jpg", full_page=True)

            with open("result.csv", mode="w", newline="") as file:
                fieldnames = result_rows[0].keys()
                dict_writer = csv.DictWriter(file, fieldnames=fieldnames)
                dict_writer.writeheader()
                dict_writer.writerows(result_rows)


asyncio.run(main())
