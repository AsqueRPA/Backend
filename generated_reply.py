import asyncio
from web_agent import WebAgent
from playwright.async_api import async_playwright
import argparse
import requests
import os
from dotenv import load_dotenv
import random

load_dotenv()

port = os.getenv("PORT")


async def main():
    async with async_playwright() as p:
        # Initialize the parser
        parser = argparse.ArgumentParser()

        # Define a custom argument type for a list of strings
        def list_of_strings(arg):
            return arg.split(",")

        # Add parameters
        parser.add_argument("-a", type=str)
        parser.add_argument("-e", type=str)
        parser.add_argument("-k", type=str)
        parser.add_argument("-q", type=str)
        parser.add_argument("-r", type=list_of_strings)

        # Parse the arguments
        account = parser.parse_args().a
        email = parser.parse_args().e
        keyword = parser.parse_args().k
        question = parser.parse_args().q
        reachouts = parser.parse_args().r

        # account = "hugozhan0802@gmail.com"
        # email = "hugozhan0802@gmail.com"
        # keyword = "Growth Lead"
        # question = "What is your biggest pain point right now when it comes to hitting your growth goals?"
        # reachouts = [
        #     "Gauri Pitke",
        #     "Alex Campbell",
        #     "Maxime RONDEAU",
        #     "Lucas Swisher",
        #     "Andy Zhu",
        #     "Marina Petrichenko (Crypto Marina)",
        #     "Andrew Hemingway",
        #     "Diana Vas",
        #     "Edouard Ugeuen",
        # ]

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

        print(proxy)

        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(proxy=proxy)
        page = await context.new_page()

        try:
            # await page.goto(
            #     "http://whatismyipaddress.com/"
            # )  # Navigate to a site to test the proxy
            # await page.screenshot(path="screenshot.jpg")
            # await page.wait_for_timeout(999999999)
            agent = WebAgent(page)

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

            for person in reachouts:

                await page.goto(
                    f"https://www.linkedin.com/messaging/?searchTerm={person}",
                    wait_until="domcontentloaded",
                )
                try:
                    await page.wait_for_selector(
                        '//a[contains(@id, "ember") and contains(@class, "ember-view msg-conversation-listitem__link msg-conversations-container__convo-item-link pl3")]',
                        timeout=5000,
                    )
                except:
                    continue
                elements = await page.query_selector_all(
                    '//a[contains(@id, "ember") and contains(@class, "ember-view msg-conversation-listitem__link msg-conversations-container__convo-item-link pl3")]'
                )
                if elements:
                    await elements[0].click()
                    await agent.process_page()
                    try:
                        await asyncio.wait_for(
                            agent.chat(
                                f"""
                            YOU HAVE TO EITHER FOLLOW UP ON THE REACHOUT OR RECORD THE RESPONSE OF THE REACHOUT, DONT USE ELEMENT NOT PRESENT
                                1. If the person doesn't have a response or the response is not related to the question, type a follow up message and ask about the {question} again in a polite way. Only after you recieve a screenshot verifying that the message is typed in the message input box, click send.
                                2. If the person has a response to the question, even if it doesnt answer the question fully, record the response with account: {account}, email: {email}, keyword: {keyword}, question: {question}, name: {person}, response: {person}'s response
                                3. If there is already a follow up message, don't do anything.

                            After you click send (which is most likely 37), DO NOT try to click send (probably 39) again, because the message is already sent and now you are clicking on a button that doesn't do anything.
                            """
                            ),
                            timeout=60,
                        )
                    except Exception as e:
                        print(e)
        except Exception as e:
            print(e)


asyncio.run(main())
