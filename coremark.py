from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.core-mark.com/")
    with page.expect_popup() as page1_info:
        page.get_by_role("list").get_by_text("Customer Logins").click()
    page1 = page1_info.value
    page1.locator("input[type=\"text\"]").click()
    page1.locator("input[type=\"text\"]").fill("021192617")
    page1.locator("input[type=\"password\"]").click()
    page1.locator("input[type=\"password\"]").fill("Dp#617")
    page1.get_by_label("Log In").click()
    with page1.expect_popup() as page2_info:
        page1.get_by_label("Create Order").click()
    page2 = page2_info.value
    page2.wait_for_timeout(5000)

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
