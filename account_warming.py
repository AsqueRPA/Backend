import asyncio
from web_agent import WebAgent
from playwright.async_api import async_playwright
import argparse
from urllib.parse import quote
import requests
import os
from dotenv import load_dotenv
import random
from send_email import send_email
import time
import html

load_dotenv()

port = os.getenv("PORT")


async def main():
    async with async_playwright() as p:
        try:
            account = "bysywbypex39934@hotmail.com"
            keyword = "Berkeley"
            last_page = 0
            password = "jKibrui7w8:SdFYV7GS0r"
            proxy = {
                "server": "http://54.215.164.150:3128",
                # uncomment later if server need auth
                # 'username': 'username',
                # 'password': 'password'
            }
            # account = "hugozhan0802@gmail.com"
            # keyword = "Berkeley"
            # last_page = 0
            # password = "huhu2001"
            # proxy = {
            #     "server": "http://54.183.164.4:3128",
            #     # uncomment later if server need auth
            #     # 'username': 'username',
            #     # 'password': 'password'
            # }

            # account = "yejoanna33@gmail.com"
            # keyword = "Berkeley"
            # last_page = 0
            # password = "jojo2002"
            # proxy = {
            #     "server": "http://54.215.135.39:3128",
            #     # uncomment later if server need auth
            #     # 'username': 'username',
            #     # 'password': 'password'
            # }

            # account = "xiaokangzhan6@gmail.com"
            # keyword = "Berkeley"
            # last_page = 0
            # password = "kangkang2001"
            # proxy = {
            #     "server": "http://54.67.17.85:3128",
            #     # uncomment later if server need auth
            #     # 'username': 'username',
            #     # 'password': 'password'
            # }

            # account = "zhanhugo0802@gmail.com"
            # keyword = "Berkeley"
            # last_page = 20
            # password = "gogo2001"
            # proxy = {
            #     "server": "http://54.193.32.52:3128",
            #     # uncomment later if server need auth
            #     # 'username': 'username',
            #     # 'password': 'password'
            # }

            # account = "didi06280828@gmail.com"
            # keyword = "Berkeley"
            # target_amount_response = 10
            # last_page = 0
            # password = "didi2001"
            # proxy = {
            #     "server": "http://54.193.112.125:3128",
            #     # uncomment later if server need auth
            #     # 'username': 'username',
            #     # 'password': 'password'
            # }

            browser = await p.chromium.launch(headless=False)

            context = await browser.new_context(proxy=proxy)
            page = await context.new_page()
            page_count = last_page + 1

            # await page.goto(
            #     "http://whatismyipaddress.com/"
            # )  # Navigate to a site to test the proxy
            # await page.screenshot(path="screenshot.jpg")
            # await page.wait_for_timeout(999999999)

            ###### login logic #######
            await page.goto("https://www.linkedin.com/")
            await page.wait_for_timeout(9999999)
            await page.wait_for_timeout(random.randint(1000, 3000))
            await page.get_by_role("link", name="Sign in").click()
            await page.wait_for_timeout(random.randint(1000, 3000))
            await page.get_by_label("Email or Phone").click()
            await page.wait_for_timeout(random.randint(1000, 3000))
            await page.get_by_label("Email or Phone").fill(account)
            await page.wait_for_timeout(random.randint(1000, 3000))
            await page.get_by_label("Password").click()
            await page.get_by_label("Password").fill(password)
            await page.wait_for_timeout(random.randint(1000, 3000))
            await page.get_by_label("Sign in", exact=True).click()
            await page.wait_for_timeout(9999999)
            print("finished logging in")
            while True:
                await page.goto(
                    f"https://www.linkedin.com/search/results/people/?keywords={quote(keyword)}&origin=SWITCH_SEARCH_VERTICAL&sid=A~y&page={page_count}",
                    wait_until="domcontentloaded",
                )
                for i in range(10):
                    start_time = time.time()  # capture the start time
                    try:
                        await page.wait_for_timeout(random.randint(1000, 3000))
                        person_selector = f"//li[contains(@class, 'reusable-search__result-container')][{i+1}]"
                        await page.wait_for_selector(person_selector, timeout=5000)
                        await page.click(person_selector, force=True, timeout=5000)
                        await page.wait_for_selector(
                            "div.pv-top-card-v2-ctas", timeout=5000
                        )
                    except Exception as e:
                        print(e)
                        await page.mouse.click(0, 0)
                        continue
                    try:
                        await page.wait_for_timeout(random.randint(1000, 3000))
                        await page.wait_for_selector(
                            "h1.text-heading-xlarge.inline.t-24.v-align-middle.break-words",
                            timeout=5000,
                        )
                        name = await page.text_content(
                            "h1.text-heading-xlarge.inline.t-24.v-align-middle.break-words",
                            timeout=5000,
                        )
                        more_actions_buttons = await page.query_selector_all(
                            f'[aria-label="More actions"]'
                        )
                        for more_action_button in more_actions_buttons:
                            try:
                                await more_action_button.click(timeout=5000)
                            except Exception as e:
                                print(e)
                        connect_buttons = await page.query_selector_all(
                            f'[aria-label="Invite {html.escape(name)} to connect"]'
                        )
                        connect_button_clicked = False
                    except Exception as e:
                        print(e)
                        continue
                    await page.wait_for_timeout(random.randint(1000, 3000))
                    for connect_button in connect_buttons:
                        try:
                            await connect_button.click(timeout=5000)
                            connect_button_clicked = True
                        except Exception as e:
                            print(e)
                    await page.wait_for_timeout(random.randint(1000, 3000))
                    if connect_button_clicked:
                        try:
                            await page.wait_for_timeout(random.randint(1000, 3000))
                            await page.wait_for_selector(
                                '[aria-label="Add a note"]', timeout=5000
                            )
                            await page.click('[aria-label="Add a note"]', timeout=5000)
                            await page.wait_for_timeout(random.randint(1000, 3000))
                            await page.type(
                                'textarea[name="message"]',
                                'Happy to connect!',
                            )
                            await page.wait_for_timeout(random.randint(1000, 3000))
                            await page.click(
                                ".artdeco-button.artdeco-button--2.artdeco-button--primary.ember-view.ml1",
                                timeout=5000,
                            )
                            await page.wait_for_timeout(random.randint(1000, 3000))
                            modal_selector = '.artdeco-modal--layer-default.ip-fuse-limit-alert'
                            modal_exists = await page.is_visible(modal_selector)
                            if modal_exists:
                                print("Connect invitation limit reached")
                                return
                        except Exception as e:
                            print(e)
                    print("back")
                    await page.go_back(wait_until="domcontentloaded", timeout=5000)
                    end_time = time.time()  # capture the end time
                    elapsed_time = end_time - start_time  # calculate elapsed time
                    print(f"The code took {elapsed_time} seconds to run.")
                page_count += 1
        except Exception as e:
            print(e)
            await page.screenshot(path="screenshot.jpg")
            send_email("hugozhan0802@gmail.com", "Error", str(e), "screenshot.jpg")

asyncio.run(main())
