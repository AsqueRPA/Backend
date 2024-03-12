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
            # Local browser
            executablePath = "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"

            userDataDir = (
                "/Users/hugozhan/Library/Application Support/Google/Chrome Canary"
            )

            browser = await p.chromium.launch_persistent_context(
                executable_path=executablePath,
                user_data_dir=userDataDir,
                headless=False,
            )

            page = await browser.new_page()
            agent = WebAgent(page)

            keyword = "nurse"

            page_count = 1

            target_amount_reachout = 100
            ####### login logic #######
            # await page.goto("https://www.linkedin.com/")
            # page.wait_for_timeout(3000)
            # await page.get_by_role("link", name="Sign in").click()
            # page.wait_for_timeout(3000)
            # await page.get_by_label("Email or Phone").click()
            # page.wait_for_timeout(3000)
            # await page.get_by_label("Email or Phone").fill("dyllan2001@berkeley.edu")
            # page.wait_for_timeout(3000)
            # await page.get_by_label("Password").click()
            # await page.get_byabel("Password").fill("dyllan2001")
            # page.wait_for_timeout(3000)
            # await page.get_by_label("Sign in", exact=True).click()
            # print('finished logging in')
            while True:
                await page.goto(
                    f"https://www.linkedin.com/search/results/people/?keywords={quote(keyword)}&origin=SWITCH_SEARCH_VERTICAL&sid=A~y&page={page_count}",
                    wait_until="domcontentloaded",
                )
                for i in range(10):
                    start_time = time.time()  # capture the start time
                    try:
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
                        await page.wait_for_selector(
                            "h1.text-heading-xlarge.inline.t-24.v-align-middle.break-words",
                            timeout=5000,
                        )
                        name = await page.text_content(
                            "h1.text-heading-xlarge.inline.t-24.v-align-middle.break-words",
                            timeout=5000,
                        )
                        await page.wait_for_timeout(5000)
                        more_actions_buttons = await page.query_selector_all(
                            f'[aria-label="More actions"]'
                        )
                        print(more_actions_buttons)
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
                    for connect_button in connect_buttons:
                        try:
                            await connect_button.click(timeout=5000)
                            connect_button_clicked = True
                        except Exception as e:
                            print(e)
                    if connect_button_clicked:
                        try:
                            await page.wait_for_timeout(random.randint(2000, 5000))
                            await page.wait_for_selector(
                                '[aria-label="Add a note"]', timeout=5000
                            )
                            await page.click('[aria-label="Add a note"]', timeout=5000)
                            await page.wait_for_timeout(random.randint(2000, 5000))
                            await page.type(
                                'textarea[name="message"]',
                                f"""Hi {name.split(" ")[0]},

I'm Hugo and just graduated from Berkeley. While I was doing research I found that healthcare professionals dislike EHR systems such Epic and Cerner. What is your take on this? 

I'd love to learn more from an industry expert. Would you also have time for a 15-minute chat?

Thanks!""",
                            )
                            await page.wait_for_timeout(random.randint(2000, 5000))
                            await page.click(
                                ".artdeco-button.artdeco-button--2.artdeco-button--primary.ember-view.ml1",
                                timeout=5000,
                            )
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
