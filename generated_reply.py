import asyncio
from web_agent import WebAgent
from playwright.async_api import async_playwright
import argparse


async def main():
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

        page = await browser.new_page()
        agent = WebAgent(page)

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
                await agent.chat(
                    f"""
                    DO THESE ONLY IF THERE ARE MESSAGES IN THE INBOX AND CHAT:
                        1. If the person doesn't have a response to the question, delete the reachout with email: {email}, keyword: {keyword}, question: {question}, name: {person}
                        2. If the person has a response to the question, record the response with email: {email}, keyword: {keyword}, question: {question}, name: {person}, response: {person}'s response
                    """
                )


asyncio.run(main())