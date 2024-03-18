import asyncio
from web_agent import JoshyTrain
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
import csv

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
        await page.get_by_placeholder("e.g. contact@email.com").fill("jack@duffl.com")
        await page.click(".btn.btn-primary.btn-medium.login-button")
        await page.fill("#password", "dufflucsb2021")
        await page.get_by_text("Log In", exact=True).click()

        await page.wait_for_timeout(5000)

        result_rows = []

        with open("kehe3.csv", mode="r") as file:
            dict_reader = csv.DictReader(file)
            for row in dict_reader:
                upc = row["upc"]

                search_bar = await page.query_selector(
                    'input[data-automation-id="edo-top-bar-search"]'
                )

                if upc:
                    await search_bar.fill(upc)
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(3000)
                    element = await page.query_selector(
                        'input[data-automation-id="edo-products-list-checkbox"]'
                    )
                    if element:
                        print("The element exists.")
                    else:
                        print("The element does not exist.")
                        row["is_out_of_stock"] = True
                        row["out_of_stock_reason"] = "not_found"
                        result_rows.append(row)
                        continue
                else:
                    row["is_out_of_stock"] = True
                    row["out_of_stock_reason"] = "not_found"
                    result_rows.append(row)
                    continue
                await page.wait_for_timeout(3000)


              
                number_of_packs = row["total_packs_ordered"]
                element_handle = await page.query_selector(
                    'input[role="spinbutton"][inputmode="numeric"]'
                )

                await element_handle.fill(number_of_packs)

                button_selector = 'button:has-text("Add")'
                await page.click(button_selector)

                modal_selector = 'div.kehe-modal:has-text("Add to Cart")'

                modal_element = await page.query_selector(modal_selector)

                if modal_element:
                    try:
                        await page.locator('kendo-textbox').click(timeout=5000)
                        await page.locator('role=textbox[name="e.g. \\\'Easter Weekend\\\'"]').fill('UCSB - 03/15')
                    except Exception as e:
                        print(e)
                    await page.locator('role=button[name="Add to Cart"]').click()
                
                result_rows.append(row)

            with open("result.csv", mode="w", newline="") as file:
                fieldnames = result_rows[0].keys()
                dict_writer = csv.DictWriter(file, fieldnames=fieldnames)
                dict_writer.writeheader()
                dict_writer.writerows(result_rows)


asyncio.run(main())

