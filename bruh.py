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
        await page.goto("https://www.linkedin.com/in/jameslabastida/")
        agent = WebAgent(page)

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
        except Exception as e:
            print(e)

        buttons = await page.query_selector_all(f'[aria-label="Invite {name} to connect"]')
        button_clicked = False
        for button in buttons:
            try:
                await button.click(timeout=5000)
                button_clicked = True
            except Exception as e:
                print(e)
        if button_clicked:
            await page.wait_for_selector(
                '[aria-label="Add a note"]', timeout=5000
            )
            await page.click('[aria-label="Add a note"]', timeout=5000)


asyncio.run(main())

