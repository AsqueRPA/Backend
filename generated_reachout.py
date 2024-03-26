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
        # Initialize the parser
        parser = argparse.ArgumentParser()

        # Add parameters
        parser.add_argument("-a", type=str)
        parser.add_argument("-e", type=str)
        parser.add_argument("-k", type=str)
        parser.add_argument("-q", type=str)
        parser.add_argument("-l", type=int)
        parser.add_argument("-t", type=int)

        # Parse the arguments
        account = parser.parse_args().a
        email = parser.parse_args().e
        keyword = parser.parse_args().k
        question = parser.parse_args().q
        last_page = parser.parse_args().l
        target_amount_reachout = parser.parse_args().t

        url = f"http://localhost:{port}/get-proxy/{account}"
        response = requests.get(url)
        if response.status_code == 200:
            response_data = response.json()
            proxy = response_data.get("proxy")
            password = proxy.get("password")
            proxy = {
                "server": proxy.get("url"),
                # uncomment later if server need auth
                # 'username': 'username',
                # 'password': 'password'
            }
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return

        # account = "didi06280828@gmail.com"
        # email = "hugozhan0802@gmail.com"
        # keyword = "Berkeley"
        # question = "Happy to connect!"
        # target_amount_response = 10
        # last_page = 0
        # password = "didi2001"
        # proxy = {
        #     "server": "http://13.52.99.7:3128",
        #     # uncomment later if server need auth
        #     # 'username': 'username',
        #     # 'password': 'password'
        # }
        print(proxy)

        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(proxy=proxy)
        page = await context.new_page()
        try:
            # await page.goto(
            #     "http://whatismyipaddress.com/"
            # )  # Navigate to a site to test the proxy
            # await page.screenshot(path="screenshot.jpg")
            # await page.goto("https://www.linkedin.com/")
            # await page.wait_for_timeout(999999999)
            agent = WebAgent(page)

            page_count = last_page + 2

            ###### login logic #######
            await page.goto("https://www.linkedin.com/")
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
            print("finished logging in")
            count = 0
            while count < target_amount_reachout:
                await page.goto(
                    f"https://www.linkedin.com/search/results/people/?keywords={quote(keyword)}&origin=SWITCH_SEARCH_VERTICAL&sid=A~y&page={page_count}",
                    wait_until="domcontentloaded",
                )
                for i in range(10):
                    start_time = time.time()  # capture the start time
                    try:
                        print(1)
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
                    # this might break
                    try:
                        print(2)
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
                    print(3)
                    await page.wait_for_timeout(random.randint(1000, 3000))
                    for connect_button in connect_buttons:
                        try:
                            await connect_button.click(timeout=5000)
                            connect_button_clicked = True
                        except Exception as e:
                            print(e)
                    print(4)
                    if connect_button_clicked:
                        try:
                            await page.wait_for_timeout(random.randint(1000, 3000))
                            await page.wait_for_selector(
                                '[aria-label="Add a note"]', timeout=5000
                            )
                            await page.click('[aria-label="Add a note"]', timeout=5000)
                            await page.wait_for_timeout(random.randint(1000, 3000))

                            # AGENT INPUT
                            await agent.chat(
                                f"""In the 'Add a note' text box, within 250 characters, write a quick introduction including the person's name if possible and ask the question: '{question}'. 
                                Be concise, don't include any placeholder text, this will be the message sent to the recipient. 
                                Somtimes you might accidentally select the search bar (usually with ID 13), usually the textbox has a smaller ID, such as 5. 
                                Don't do anything else because it will disrupt the next step. 
                                If there is text in the textbox already, it means you have already filled in the message, don't try to fill in the message again"""
                            )

                            # # MANUAL INPUT
                            # await page.type(
                            #     'textarea[name="message"]',
                            #     'Happy to connect!',
                            # )

                            await page.wait_for_timeout(random.randint(1000, 3000))
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
                            count += 1
                        except Exception as e:
                            print(e)
                    print("back")
                    await page.go_back(wait_until="domcontentloaded", timeout=5000)
                    end_time = time.time()  # capture the end time
                    elapsed_time = end_time - start_time  # calculate elapsed time
                    print(f"The code took {elapsed_time} seconds to run.")

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
        except Exception as e:
            print(e)
            await page.screenshot(path="screenshot.jpg")
            send_email("hugozhan0802@gmail.com", "Error", str(e), "screenshot.jpg")


asyncio.run(main())
