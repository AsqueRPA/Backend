import asyncio
import math
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

load_dotenv()

port = os.getenv("PORT")


async def main():
    async with async_playwright() as p:
        # Initialize the parser
        parser = argparse.ArgumentParser()

        # Add parameters
        parser.add_argument("-a", type=str)
        parser.add_argument("-e", type=str)
        parser.add_argument("-k", type=str)
        parser.add_argument("-q", type=str)
        parser.add_argument("-t", type=int)
        parser.add_argument("-l", type=int)

        # Parse the arguments
        account = parser.parse_args().a
        email = parser.parse_args().e
        keyword = parser.parse_args().k
        question = parser.parse_args().q
        target_amount_response = parser.parse_args().t
        last_page = parser.parse_args().l

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
        agent = WebAgent(page)

        page_count = last_page + 1

        target_amount_reachout = 5 * target_amount_response
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
            try:
                await page.goto(
                    f"https://www.linkedin.com/search/results/people/?keywords={quote(keyword)}&origin=SWITCH_SEARCH_VERTICAL&sid=A~y&page={page_count}",
                    wait_until="domcontentloaded",
                )
            except Exception as e:
                print(e)
                await page.screenshot(path="screenshot.png")
                send_email("hugozhan0802@gmail.com", "Error", str(e), "screenshot.png")
                break
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
                # this might break
                try:
                    await page.wait_for_selector(
                        "h1.text-heading-xlarge.inline.t-24.v-align-middle.break-words",
                        timeout=5000,
                    )
                    name = await page.text_content(
                        "h1.text-heading-xlarge.inline.t-24.v-align-middle.break-words",
                        timeout=5000,
                    )
                except Exception as e:
                    print(e)
                    continue
                buttons = await page.query_selector_all(f'[aria-label="Invite {name} to connect"]')
                button_clicked = False
                for button in buttons:
                    try:
                        await button.click(timeout=5000)
                        button_clicked = True
                    except Exception as e:
                        print(e)
                if button_clicked:
                    try:
                        await page.wait_for_timeout(random.randint(2000, 5000))
                        await page.wait_for_selector(
                            '[aria-label="Add a note"]', timeout=5000
                        )
                        await page.click('[aria-label="Add a note"]', timeout=5000)
                        await page.wait_for_timeout(random.randint(2000, 5000))
                        await agent.process_page()
                        await agent.chat(
                            f"In the 'Add a note' text box, within 250 characters, write a quick introduction including the person's name if possible and ask the question: {question}, don't include any placeholder text, this will be the message sent to the recipient. somtimes you might accidentally select the search bar (usually with ID 13), usually the textbox has a smaller ID, such as 5. Don't do anything else because it will disrupt the next step. If there is text in the textbox already, it means you have already filled in the message, don't try to fill in the message again"
                        )
                        await page.wait_for_timeout(random.randint(2000, 5000))
                        await page.click(
                            ".artdeco-button.artdeco-button--2.artdeco-button--primary.ember-view.ml1",
                            timeout=5000,
                        )
                        linkedinUrl = page.url
                        url = f"http://localhost:{port}/record-reachout"
                        data = {
                            "account": account,
                            "email": email,
                            "keyword": keyword,
                            "question": question,
                            "name": name,
                            "linkedinUrl": linkedinUrl,
                        }
                        response = requests.post(url, json=data)
                        print(response.status_code)
                        print(response.text)
                    except Exception as e:
                        print(e)
                print("back")
                await page.go_back(wait_until="domcontentloaded", timeout=5000)
                end_time = time.time()  # capture the end time
                elapsed_time = end_time - start_time  # calculate elapsed time
                print(f"The code took {elapsed_time} seconds to run.")
            url = f"http://localhost:{port}/amount-reachout"
            data = {
                "account": account,
                "email": email,
                "keyword": keyword,
                "question": question,
            }
            response = requests.post(url, json=data)
            if response.status_code == 200:
                response_data = response.json()
                current_amount_reachout = response_data.get("currentAmountReachout")
                if current_amount_reachout >= target_amount_reachout:
                    break
            else:
                print(f"Error: {response.status_code}")
                print(response.text)

            url = f"http://localhost:{port}/update-last-page"
            data = {
                "account": account,
                "email": email,
                "keyword": keyword,
                "question": question,
                "lastPage": page_count,
            }
            response = requests.post(url, json=data)
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(response.text)
            page_count += 1


try:
    asyncio.run(main())
except Exception as e:
    print(e)
    send_email("hugozhan0802@gmail.com", "Error", str(e), "screenshot.png")
