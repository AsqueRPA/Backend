from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.linkedin.com/")
    page.get_by_role("link", name="Sign in").click()
    page.get_by_label("Email or Phone").click()
    page.get_by_label("Email or Phone").fill("dyllan2001@berkeley.edu")
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("dyllan2001")
    page.get_by_label("Sign in", exact=True).click()
    page.wait_for_timeout(50000)

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
