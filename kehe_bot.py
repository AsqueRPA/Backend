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


"""
UPC and if UPC doesn't work I'll see if there's a different UPC for the item online and try that
And if that doesn't work, I'll do it like a word search but I don't spend more than like two minutes. 
If I'm doing that I'll just say that I didn't find the item
"""

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
                row["updated_price"] = ""
                row["updated_upc"] = ""
                item_name = row["product_name"]
                upc = row["upc"]

                joshyTrain = JoshyTrain(page)
                if upc:
                    await joshyTrain.chat(f"search {upc} in the search bar")
                else:
                    await joshyTrain.chat(f"search {item_name} in the search bar")
                response = await joshyTrain.chat(
                    f"""tell me the name of the item in JSON format that is most similar to {item_name}.
                    Consider similarities in brand, product name, flavor, and size. 
                    Respond in the following JSON format: 
                    {{"name": "exact name of the item", "reason": "your reason for choosing this item"}}"""
                )
                data = joshyTrain.extract_json(response)
                if data and "name" in data:
                    name = data["name"]
                else:
                    name = item_name
                number_of_packs = row["total_packs_ordered"]
                await joshyTrain.chat(
                    f"For {name}, put {number_of_packs} for amount and click 'Add'. if it asks you for the order name, put 'test order' and click 'Add to Cart', otherwise do nothing."
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
