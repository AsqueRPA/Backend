import asyncio
from playwright.async_api import async_playwright
import argparse
from web_agent import WebAgent


async def reply():
    async with async_playwright() as p:
        # Initialize the parser
        parser = argparse.ArgumentParser()

        # Define a custom argument type for a list of strings
        def list_of_strings(arg):
            return arg.split(",")

        # Add parameters
        parser.add_argument("-e", type=str)
        parser.add_argument("-k", type=str)
        parser.add_argument("-q", type=str)
        parser.add_argument("-r", type=list_of_strings)

        # Parse the arguments
        email = parser.parse_args().e
        keyword = parser.parse_args().k
        question = parser.parse_args().q
        reachouts = parser.parse_args().r

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

        for person in reachouts:
            await agent.chat(
                f"go to https://www.linkedin.com/messaging/?searchTerm={person}"
            )
            await agent.chat("click on the first message if it is in the inbox")
            await agent.chat(
                f"""
                DO THESE ONLY IF THERE ARE MESSAGES IN THE INBOX AND CHAT:
                    2. If the person doesn't have a response to the question, delete the reachout with email: {email}, keyword: {keyword}, question: {question}, name: {person}
                    1. If the person has a response to the question, record the response with email: {email}, keyword: {keyword}, question: {question}, name: {person}, response: {person}'s response
                """
            )


asyncio.run(reply())
