from playwright.sync_api import Playwright, sync_playwright
import asyncio
from web_agent import JoshyTrain
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
import csv
import re

load_dotenv()

port = os.getenv("PORT")


async def search(page, item_name, search_terms=[]):
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
        response = await joshyTrain.chat(
            f"""{search_instruction}, DO: INPUT different search terms into the search bar for {item_name}, you have already tried {search_terms}.

            Just try once and then return one of the following:
            1. If you end up finding the product, then you don't need to do anything else and just return 'product found', NEVER DO THIS WHEN THE PAGE SAIDS "No Record Found"
            2. otherwise return the searchTerm in the format {{"searchTerm": "exact search term you put as the input"}} when you don't find the product or the product page is empty

            the above is your ONLY TWO OPTIONS AFTER ATTEMPTING TO INPUT INTO THE SEARCH BAR, never output {{"searchTerm": "exact search term you put as the input"}} if you haven't outputted {{"input": {{"select": "ID", "text": "exact search term you put as the input"}}}}

            if you don't follow the above, then the program will not work.
            """
        )
        data = joshyTrain.extract_json(response)
        if data and "searchTerm" in data:
            search_term = data["searchTerm"]
            search_terms.append(search_term)
        else:
            break

    # # Manual Search
    # await page.get_by_placeholder("Search Product").fill("funyuns")
    # await page.keyboard.press("Enter")
    # await page.wait_for_timeout(5000)

    # return 2

    item_dict = {}
    i = 2
    while True:
        try:
            item_div = await page.query_selector(
                f".MuiGrid-root-128.product-tile.MuiGrid-item-130.MuiGrid-grid-xs-6-168.MuiGrid-grid-sm-4-180.MuiGrid-grid-md-4-194.MuiGrid-grid-lg-3-207:nth-of-type({i}) .productlist-img"
            )
            print(item_div)
            await item_div.click()
            response = await joshyTrain.chat(
                f"""
give your confidence level on this current item being the item, {item_name}, that we are looking for, 0-10, 10 being 100% confident, 0 being no confidence at all.
consider the packaging, the name, the brand, the flavor, the size, and all other information you can get from the item details pop up to help you make this rating
For example you should have low confidence that Cheetos Crunchy - Cheddar Jalapeno - 3.25 oz and Cheetos Crunchy Cheese Flavored Snacks are the same thing
respond in the following JSON format:
{{
"index": {i}
"confidence": "your confidence level",
"reasoning": "your reasoning"
}}
"""
            )
            data = joshyTrain.extract_json(response)
            if data and "confidence" in data:
                item_dict[i] = data
            close_icon = await page.query_selector(
                'img[src="a8d398bb099ac1e54d401925030b9aa2.svg"]'
            )
            await close_icon.click()
        except Exception as e:
            print("Finished eval")
            break
        i += 1
    sorted_items = sorted(
        item_dict.items(), key=lambda item: -int(item[1]["confidence"])
    )

    if len(sorted_items) == 0:
        if len(search_terms) <= minimum_search_terms:
            return await search(page, item_name, search_terms)
        else:
            search_terms = []
            return 0
    elif int(sorted_items[0][1]["confidence"]) < minimum_confidence:
        return await search(page, item_name, search_terms)
    else:
        search_terms = []
        return sorted_items[0][0]


async def main():
    async with async_playwright() as p:
        # Local browser
        executablePath = (
            "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"
        )

        userDataDir = "/Users/hugozhan/Library/Application Support/Google/Chrome Canary"

        browser = await p.chromium.launch_persistent_context(
            executable_path=executablePath,
            user_data_dir=userDataDir,
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

        with open("orders.csv", mode="r") as file:
            dict_reader = csv.DictReader(file)
            # [name, upc, order status]
            cart = []
            for row in dict_reader:
                print(row)
                item_name = row["product_name"]
                i = await search(page, item_name)
                print(i)

                if not i:
                    print("No Record Found")
                    cart = [item_name, upc_number, "No Record Found"]
                    continue

                item_div = await page.query_selector(
                    f".MuiGrid-root-128.product-tile.MuiGrid-item-130.MuiGrid-grid-xs-6-168.MuiGrid-grid-sm-4-180.MuiGrid-grid-md-4-194.MuiGrid-grid-lg-3-207:nth-of-type({i}) .productlist-img"
                )

                print(item_div)

                await item_div.click()

                await page.wait_for_timeout(2000)
                await page.screenshot(path="screenshot.jpg", full_page=True)

                product_details_div = await page.query_selector('.MuiGrid-root-128.product-detail-wrapper-inner')

                upc_number = await product_details_div.query_selector('.product-info-text:has-text("UPC:")')
                
                upc_number = re.search(r'UPC:\s*(\d+)', await upc_number.inner_text())
                if upc_number:
                    upc_number = upc_number.group(1)  # This is your UPC number
    
                out_of_stock = await page.query_selector(".product-out-stock.list")
                if out_of_stock:
                    print("Out of Stock")
                    cart.append([item_name, upc_number, "Out of Stock"])
                else:
                    input_element = await page.query_selector(
                        ".product-detail-wrapper .MuiInputBase-input-395.MuiOutlinedInput-input-382.MuiInputBase-inputAdornedEnd-400.MuiOutlinedInput-inputAdornedEnd-386"
                    )
                    print(input_element)
                    number_of_packs = row["total_packs_ordered"]
                    await input_element.fill(number_of_packs)
                    await page.keyboard.press("Tab")
                    cart = [item_name, upc_number, f"Added {number_of_packs} to Cart"]

                    await page.wait_for_timeout(2000)
                    await page.screenshot(path="screenshot.jpg", full_page=True)

                close_icon = await page.query_selector(
                    'img[src="a8d398bb099ac1e54d401925030b9aa2.svg"]'
                )
                await close_icon.click()

                await page.wait_for_timeout(2000)
                await page.screenshot(path="screenshot.jpg", full_page=True)
                print(cart)

            cart_icon = await page.query_selector('img[src="www/images/cart.svg"]')
            await cart_icon.click()

            await page.screenshot(path="screenshot.jpg", full_page=True)
            with open("result.csv", "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerows(cart.items())


asyncio.run(main())