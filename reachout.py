import asyncio
from playwright.async_api import async_playwright
import argparse
from urllib.parse import quote
from web_agent import WebAgent
import requests


async def reach_out():
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

        ## Remote browser
        # userDataDir = "/home/ubuntu/.mozilla/firefox/96tbgq4x.default-release"

        # browser = await p.firefox.launch_persistent_context(
        #     userDataDir,
        #     headless=False,
        # )

        page = await browser.new_page()
        agent = WebAgent(page)

        page_count = last_page + 1

        target_amount_reachout = 5 * target_amount_response

        await agent.chat("go to https://www.linkedin.com/in/nghia-hoang/")
        await agent.chat("click on the 'Connect' button")

        # while True:
        #     await agent.chat(
        #         f"go to https://www.linkedin.com/search/results/people/?keywords={quote(keyword)}&origin=SWITCH_SEARCH_VERTICAL&sid=A~y&page={page_count}"
        #     )
        #     for i in range(10):
        #         await agent.chat(f"list the ten people's names")
        #         await agent.chat(
        #             f"click person {i + 1}, sometimes it doesn't work in the first try, so click again when you don't see the person's profile"
        #         )
        #         await agent.chat(
        #             "skip these steps if we are already connected (the button saids 'Message') or the invitation is pending (the button saids 'Pending'), otherwise click the 'Connect' button and don't do anything else because it will disrupt the next step"
        #         )
        #         await agent.chat(
        #             "skip this step if the previous step wasn't performed, otherwise click the 'Add a note' button and don't do anything else because it will disrupt the next step"
        #         )
        #         await agent.chat(
        #             f"skip this step if the previous step wasn't performed, otherwise in the text box, within 300 characters, write a quick introduction and ask the question: {question}, don't include any placeholder text, this will be the message sent to the recipient. somtimes you might accidentally select the search bar (usually with ID 13), usually the textbox has a smaller ID, such as 5. Don't do anything else because it will disrupt the next step"
        #         )
        #         await agent.chat(
        #             f"skip this step if the previous step wasn't performed, otherwise click send."
        #         )
        #         await agent.chat(
        #             f"skip this step if the previous step wasn't performed, otherwise use JSON to record the reachout with email: {email}, keyword: {keyword}, question: {question}, name: person's name"
        #         )
        #         await agent.chat("if you are not on the people list page, navigation back to people list page")
        #     url = "http://localhost/amount-reachout"
        #     data = {
        #         "email": email,
        #         "keyword": keyword,
        #         "question": question,
        #     }
        #     response = requests.post(url, json=data)
        #     if response.status_code == 200:
        #         response_data = response.json()
        #         current_amount_reachout = response_data.get("currentAmountReachout")
        #         if current_amount_reachout >= target_amount_reachout:
        #             break
        #     else:
        #         print(f"Error: {response.status_code}")
        #         print(response.text)

        #     url = "http://localhost/update-last-page"
        #     data = {
        #         "email": email,
        #         "keyword": keyword,
        #         "question": question,
        #         "lastPage": page_count,
        #     }
        #     response = requests.post(url, json=data)
        #     if response.status_code != 200:
        #         print(f"Error: {response.status_code}")
        #         print(response.text)
        #     page_count += 1


asyncio.run(reach_out())
