import asyncio
from playwright.async_api import async_playwright

async def run_browser_instance(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=False to see the browser
        page = await browser.new_page()
        await page.goto(url)
        # Add your Playwright interaction code here
        # For example, you can scrape data, fill forms, click buttons, etc.
        await page.wait_for_timeout(10000)
        print(f"Completed: {url}")
        await browser.close()

async def main():
    urls = ['https://example.com', 'https://example.org', 'https://example.net']  # List your URLs here
    tasks = []
    for url in urls:
        task = asyncio.create_task(run_browser_instance(url))
        tasks.append(task)
    await asyncio.gather(*tasks)

# Run the script
asyncio.run(main())
