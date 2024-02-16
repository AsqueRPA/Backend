import asyncio
from web_agent import WebAgent
from playwright.async_api import async_playwright
import argparse
from urllib.parse import quote
import requests
import os
from dotenv import load_dotenv

load_dotenv()

port = os.getenv("PORT")


async def main():
    async with async_playwright() as p:
        # Initialize the parser
        parser = argparse.ArgumentParser()

        # Add parameters
        parser.add_argument("-e", type=str)
        parser.add_argument("-k", type=str)
        parser.add_argument("-q", type=str)
        parser.add_argument("-t", type=int)
        parser.add_argument("-l", type=int)

        # Parse the arguments
        email = parser.parse_args().e
        keyword = parser.parse_args().k
        question = parser.parse_args().q
        target_amount_response = parser.parse_args().t
        last_page = parser.parse_args().l

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
        agent = WebAgent(page)

        page_count = last_page + 1

        target_amount_reachout = 5 * target_amount_response

        while True:
            await page.goto(
                f"https://www.linkedin.com/search/results/people/?keywords={quote(keyword)}&origin=SWITCH_SEARCH_VERTICAL&sid=A~y&page={page_count}",
                wait_until="domcontentloaded",
            )
            for i in range(10):
                person_selector = f"//li[contains(@class, 'reusable-search__result-container')][{i+1}]"
                await page.wait_for_selector(person_selector)
                await page.click(person_selector, force=True)
                await page.wait_for_selector("div.pv-top-card-v2-ctas")
                await page.wait_for_selector(
                    "h1.text-heading-xlarge.inline.t-24.v-align-middle.break-words"
                )
                name = await page.text_content(
                    "h1.text-heading-xlarge.inline.t-24.v-align-middle.break-words"
                )
                await page.wait_for_timeout(5000)
                connect_button = await page.query_selector(
                    "button.artdeco-button.artdeco-button--2.artdeco-button--primary.ember-view.pvs-profile-actions__action"
                )
                if connect_button and (await connect_button.text_content()).strip() == "Connect":
                    try:
                        await connect_button.click()
                        await page.wait_for_selector(
                            '[aria-label="Add a note"]', timeout=5000
                        )
                        await page.click('[aria-label="Add a note"]')
                        await agent.process_page()
                        await agent.chat(
                            f"In the custom message text box, within 300 characters, write a quick introduction and ask the question: {question}, don't include any placeholder text, this will be the message sent to the recipient. somtimes you might accidentally select the search bar (usually with ID 13), usually the textbox has a smaller ID, such as 5. Don't do anything else because it will disrupt the next step"
                        )
                        await page.click(
                            ".artdeco-button.artdeco-button--2.artdeco-button--primary.ember-view.ml1"
                        )

                        url = f"http://localhost:{port}/record-reachout"
                        data = {
                            "email": email,
                            "keyword": keyword,
                            "question": question,
                            "name": name,
                        }
                        response = requests.post(url, json=data)
                        print(response.status_code)
                        print(response.text)
                    except Exception as e:
                        print(e)
                print("back")
                await page.go_back(wait_until="domcontentloaded")
            url = "http://localhost/amount-reachout"
            data = {
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

            url = "http://localhost/update-last-page"
            data = {
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


asyncio.run(main())
