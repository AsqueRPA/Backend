import asyncio
from web_agent import JoshyTrain
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
import csv
import re
import argparse
from openai import OpenAI

load_dotenv()

port = os.getenv("PORT")
model = OpenAI()
model.timeout = 30


async def chat(prompt):
    print("User:", prompt)
    response = model.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
        max_tokens=4096,
    )
    message = response.choices[0].message
    message_text = message.content
    print("Assistant:", message_text)
    return message_text


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
                item_name = row["product_name"]
                upc = row["upc"]

                joshyTrain = JoshyTrain(page)
                # Assuming 'page' is your page object
                search_bar = await page.query_selector(
                    'input[data-automation-id="edo-top-bar-search"]'
                )
                element = None
                if upc:
                    await search_bar.fill(upc)
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(3000)
                    element = await page.query_selector(
                        'input[data-automation-id="edo-products-list-checkbox"]'
                    )
                if element:

                    # number_of_packs = row["total_packs_ordered"]
                    # # Select the element
                    # element_handle = await page.query_selector(
                    #     'input[role="spinbutton"][inputmode="numeric"]'
                    # )

                    # # Fill the element with the desired value
                    # await element_handle.fill(number_of_packs)

                    # # Find the button by its text and class. Ensure the class name used is unique to the button.
                    # button_selector = 'button:has-text("Add")'
                    # # Click the button
                    # await page.click(button_selector)

                    # # Selector for the modal based on its class and the title text contained within
                    # modal_selector = 'div.kehe-modal:has-text("Add to Cart")'

                    # # Attempt to find the modal element
                    # modal_element = await page.query_selector(modal_selector)

                    # order_name = "UCSB - 03/15"

                    # # Check if the modal element exists
                    # if modal_element:
                    #     try:
                    #         await page.locator("kendo-textbox").click(timeout=5000)
                    #         await page.locator(
                    #             "role=textbox[name=\"e.g. \\'Easter Weekend\\'\"]"
                    #         ).fill(order_name)
                    #     except Exception as e:
                    #         print(e)
                    #     await page.locator('role=button[name="Add to Cart"]').click()

                    brand_name_selector = 'div[data-automation-id="edo-products-list-item-supplier-name"] strong'
                    product_name_selector = (
                        'div[_ngcontent-ng-c2225601486][data-automation-id="edo-products-list-item-product-name"]'
                    )

                    brand_name_element = await page.query_selector(brand_name_selector)
                    brand_name = (
                        await brand_name_element.text_content()
                        if brand_name_element
                        else "[Brand name not found]"
                    )

                    product_name_element = await page.query_selector(
                        product_name_selector
                    )
                    product_name = (
                        await product_name_element.text_content()
                        if product_name_element
                        else "[Product name not found]"
                    )

                    row["name_ordered"] = brand_name + " " + product_name
                    print(row["name_ordered"])
                else:
                    await search_bar.fill(item_name)
                    await page.keyboard.press("Enter")

                    await page.wait_for_timeout(3000)
                    brand_name_selector = 'div[data-automation-id="edo-products-list-item-supplier-name"] strong'
                    product_name_selector = (
                        'div[data-automation-id="edo-products-list-item-product-name"]'
                    )

                    brand_name_elements = await page.query_selector_all(
                        brand_name_selector
                    )
                    product_name_elements = await page.query_selector_all(
                        product_name_selector
                    )

                    all_items = []

                    for i in range(min(25, len(brand_name_elements))):
                        brand_name = (
                            await brand_name_elements[i].text_content()
                            if i < len(brand_name_elements)
                            else "[Brand name not found]"
                        )
                        product_name = (
                            await product_name_elements[i].text_content()
                            if i < len(product_name_elements)
                            else "[Product name not found]"
                        )

                        full_name = f"{brand_name} {product_name}"

                        all_items.append({i: full_name})

                    await page.wait_for_timeout(300000000)

                    # gpt finds cloest product with name

                    prompt = f"""
                    given the python dict, please return the key where the value of this key is closest to {item_name} in the {card_text_map}. 

                    give your confidence level on this from 0-10, which is your combined score from the following criteria:

            the product name:
            - 3pts if the product name is exactly correct 
            - 2pts if the product name is close to the correct product name, for example, if the item name is Cheetos Crunchy - Cheddar Jalapeno - 3.25 oz, then Cheetos is close to the correct product name (Cheetos Crunchy is the correct product name)
            - 1pt if the product name is somewhat close to the correct product name
            - 0pt if the product name is not close to the correct product name

            the flavor:
            - 3pts if the flavor is exactly correct 
            - 2pts if the flavor is close to the correct flavor, for example, if the item name is Cheetos Crunchy - Cheddar Jalapeno - 3.25 oz, then Jalapeno is close to the correct flavor (Cheddar Jalapeno is the correct flavor), only having Cheedar is not close to the correct flavor because the entire line of snacks is cheese flavored
            - 1pt if the flavor is somewhat close to the correct flavor
            - 0pt if the flavor is not close to the correct flavor

            the size:
            - 4pts if the size is exactly correct 
            - 3pts if the size is close to the correct size, if the size difference is within 0.5 oz
            - 2pt if the size is somewhat close to the correct size, if the size difference is within 1 oz
            - 1pt if the size is somewhat close to the correct size, if the size difference is within 2 oz
            - 0pt if the size is not close to the correct size

            Add the score up and ONLY return the following JSON format:
            {{
            "key": "the key of the item that matches {item_name}",
            "reasoning": "your reasoning",
            "confidence": "your combined confidence level",
            }}

            have your explanation inside the JSON, your response should only contain the JSON and NOTHING ELSE
            """
                    response = await chat(prompt)
                    response = await chat(prompt)
                    data = joshyTrain.extract_json(response)
                    confidence = int(data["confidence"])
                    i = int(data["key"])
                    item_div = await page.query_selector(
                        f".MuiGrid-root-128.product-tile.MuiGrid-item-130.MuiGrid-grid-xs-6-168.MuiGrid-grid-sm-4-180.MuiGrid-grid-md-4-194.MuiGrid-grid-lg-3-207:nth-of-type({i}) .productlist-img"
                    )
                    await item_div.click()
                    prompt = f"""Are these two the same item? {item_name} and {all_items[i]}, little difference in size by 1oz or smaller is okay. Respond with the following JSON format: {{"answer": "true or false", "reasoning": "your reasoning"}}"""
                    response = await joshyTrain.chat(prompt)

                result_rows.append(row)

            with open("result.csv", mode="w", newline="") as file:
                fieldnames = result_rows[0].keys()
                dict_writer = csv.DictWriter(file, fieldnames=fieldnames)
                dict_writer.writeheader()
                dict_writer.writerows(result_rows)


asyncio.run(main())
