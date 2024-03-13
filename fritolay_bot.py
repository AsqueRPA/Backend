import asyncio
from web_agent import JoshyTrain
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
import csv
import re

load_dotenv()

port = os.getenv("PORT")


async def search(page, item_name, search_terms):
    joshyTrain = JoshyTrain(page)
    minimum_confidence = 7
    minimum_search_terms = 3
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

    # # Manual Search
    # await page.get_by_placeholder("Search Product").fill("Cheetos Crunchy")
    # await page.keyboard.press("Enter")
    # await page.wait_for_timeout(5000)

    # return 2

    card_text_map = {}
    card_titles = await page.query_selector_all(".pro-list-title-mob")
    for index, card_title in enumerate(card_titles):
        await card_title.click()
        await page.wait_for_selector(".product-title", state="visible")
        modal_text = await page.inner_text(".product-title")
        card_text_map[index + 2] = modal_text
        await page.click('[aria-label="close"]')
        await page.wait_for_timeout(
            2000
        )  # Wait for the modal to close, adjust as needed

    if len(card_text_map) == 0:
        if len(search_terms) <= minimum_search_terms:
            return await search(page, item_name, search_terms)
        else:
            return 0

    prompt = f"""
    given a python dict, please return the key where the value of this key is {item_name} in the {card_text_map}. 
    Respond with the following JSON format:
    {{"index": "the index of the item that matches {item_name}"}}
    """
    response = await joshyTrain.chat(prompt)
    data = joshyTrain.extract_json(response)
    i = int(data["index"])
    item_div = await page.query_selector(
        f".MuiGrid-root-128.product-tile.MuiGrid-item-130.MuiGrid-grid-xs-6-168.MuiGrid-grid-sm-4-180.MuiGrid-grid-md-4-194.MuiGrid-grid-lg-3-207:nth-of-type({i}) .productlist-img"
    )
    await item_div.click()
    response = await joshyTrain.chat(
        f"""
give your confidence level on this current item being the item, {item_name}, that we are looking for from 0-10, which is your combined score from the following criteria:

the brand name:
- 2pt if the brand name is in the item name
- 0pt if the brand name is not in the item name

the product name:
- 2pts if the product name is exactly correct 
- 1pt if the product name is close to the correct product name, for example, if the item name is Cheetos Crunchy - Cheddar Jalapeno - 3.25 oz, then Cheetos is close to the correct product name (Cheetos Crunchy is the correct product name)
- 0pt if the product name is not close to the correct product name

the flavor:
- 3pts if the flavor is exactly correct 
- 2pts if the flavor is close to the correct flavor, for example, if the item name is Cheetos Crunchy - Cheddar Jalapeno - 3.25 oz, then Jalapeno or Cheddar is close to the correct flavor (Cheddar Jalapeno is the correct flavor)
- 1pt if the flavor is somewhat close to the correct flavor
- 0pt if the flavor is not close to the correct flavor

the size:
- 2pts if the size is exactly correct 
- 1pt if the size is close to the correct size, for example, if the item name is 3.25 oz, then 3 oz or 4 oz is close to the correct size
- 0pt if the size is not close to the correct size

the packaging:
- 1pt if the packaging is correct, for example, if the item name is Cheetos Crunchy - Cheddar Jalapeno, then the packaging should be green and yellow
- 0pt if the packaging is not correct, for example, if the item name is Cheetos Crunchy - Cheddar Jalapeno, then the packaging should not be red and blue

Add the score up and return the following JSON format:
{{
"confidence": "your combined confidence level",
"reasoning": "your reasoning"
}}
"""
    )
    close_icon = await page.query_selector(
        'img[src="a8d398bb099ac1e54d401925030b9aa2.svg"]'
    )
    await close_icon.click()
    data = joshyTrain.extract_json(response)
    if int(data["confidence"]) <= minimum_confidence:
        return await search(page, item_name, search_terms)
    else:
        return i


async def main():
    async with async_playwright() as p:
        # # Local browser
        # executablePath = (
        #     "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"
        # )

        # userDataDir = "/Users/hugozhan/Library/Application Support/Google/Chrome Canary"

        # browser = await p.chromium.launch_persistent_context(
        #     executable_path=executablePath,
        #     user_data_dir=userDataDir,
        #     headless=False,
        # )

        # Remote browser
        userDataDir = "/home/ubuntu/.mozilla/firefox/96tbgq4x.default-release"

        browser = await p.firefox.launch_persistent_context(
            userDataDir,
            headless=False,
        )

        page = await browser.new_page()
        ## LOGGING IN
        await page.goto("https://shop.fls2u.com/login")
        await page.wait_for_timeout(2000)
        # await page.get_by_text("Accept All Cookies", exact=True).click()
        await page.get_by_label("Username / Email*").click()
        await page.get_by_label("Username / Email*").fill("jack@duffl.com")
        await page.get_by_label("Password*").click()
        await page.get_by_label("Password*").fill("dufflucsb2021")
        await page.get_by_label("login", exact=True).click()

        await page.wait_for_timeout(8000)

        result_rows = []

        with open("orders.csv", mode="r") as file:
            dict_reader = csv.DictReader(file)
            # [name, upc, order status]
            for row in dict_reader:
                row["updated_price"] = ""
                row["updated_upc"] = ""
                item_name = row["product_name"]
                # item_name = "Cheetos Crunchy - Cheddar Jalapeno - 3.25 oz"
                i = await search(page, item_name, [])
                print(i)

                if not i:
                    print("not_found")
                    row["out_of_stock_reason"] = "not_found"
                    continue

                item_div = await page.query_selector(
                    f".MuiGrid-root-128.product-tile.MuiGrid-item-130.MuiGrid-grid-xs-6-168.MuiGrid-grid-sm-4-180.MuiGrid-grid-md-4-194.MuiGrid-grid-lg-3-207:nth-of-type({i}) .productlist-img"
                )

                print(item_div)

                await item_div.click()

                await page.wait_for_timeout(2000)
                await page.screenshot(path="screenshot.jpg", full_page=True)

                product_details_div = await page.query_selector(
                    ".MuiGrid-root-128.product-detail-wrapper-inner"
                )

                upc_number = await product_details_div.query_selector(
                    '.product-info-text:has-text("UPC:")'
                )
                upc_number = re.search(r"UPC:\s*(\d+)", await upc_number.inner_text())
                if upc_number:
                    upc_number = upc_number.group(1)
                    if upc_number != row["upc"]:
                        row["updated_upc"] = upc_number

                product_cost = await product_details_div.query_selector(".product-cost")
                product_cost = re.search(r"Cost:\s*\$(\d+\.\d+)", "Cost: $1.88")
                if product_cost:
                    product_cost = product_cost.group(1)
                    if product_cost != row["pack_price"]:
                        row["updated_price"] = product_cost

                out_of_stock = await page.query_selector(".product-out-stock.list")
                if out_of_stock:
                    print("product_oos")
                    row["is_out_of_stock"] = True
                    row["out_of_stock_reason"] = "product_oos"
                else:
                    input_element = await page.query_selector(
                        ".product-detail-wrapper .MuiInputBase-input-395.MuiOutlinedInput-input-382.MuiInputBase-inputAdornedEnd-400.MuiOutlinedInput-inputAdornedEnd-386"
                    )
                    print(input_element)
                    number_of_packs = row["total_packs_ordered"]
                    await input_element.fill(number_of_packs)
                    await page.keyboard.press("Tab")

                    await page.wait_for_timeout(2000)
                    await page.screenshot(path="screenshot.jpg", full_page=True)

                close_icon = await page.query_selector(
                    'img[src="a8d398bb099ac1e54d401925030b9aa2.svg"]'
                )
                await close_icon.click()

                await page.wait_for_timeout(2000)
                await page.screenshot(path="screenshot.jpg", full_page=True)
                print(row)
                result_rows.append(row)

            cart_icon = await page.query_selector('img[src="www/images/cart.svg"]')
            await cart_icon.click()

            await page.screenshot(path="screenshot.jpg", full_page=True)
            with open("result.csv", mode="w", newline="") as file:
                fieldnames = result_rows[0].keys()
                dict_writer = csv.DictWriter(file, fieldnames=fieldnames)
                dict_writer.writeheader()
                dict_writer.writerows(result_rows)


asyncio.run(main())
