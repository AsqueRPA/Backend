from openai import OpenAI
import openai
from base64 import b64encode
import json
from dotenv import load_dotenv
import asyncio
from playwright.async_api import async_playwright
from tarsier import Tarsier, GoogleVisionOCRService
import time
import re
import os

load_dotenv()

google_cloud_credentials = json.loads(os.getenv("GOOGLE_CLOUD_CREDENTIALS"))

ocr_service = GoogleVisionOCRService(google_cloud_credentials)
tarsier = Tarsier(ocr_service)

model = OpenAI()
model.timeout = 30


class WebAgent:
    def __init__(self, page) -> None:
        self.url = None
        self.base64_image = None
        self.tag_to_xpath = {}
        self.page_text = ""
        self.instructions = """
            You are a website crawler. You will be given instructions on what to do by browsing. You are connected to a web browser and you will be given the screenshot and the text representation of the website you are on. 
            You can interact with the website by clicking on links, filling in text boxes, and going to a specific URL.
            
            [#ID]: text-insertable fields (e.g. textarea, input with textual type)
            [@ID]: hyperlinks (<a> tags)
            [$ID]: other interactable elements (e.g. button, select)
            [ID]: plain text (if you pass tag_text_elements=True)

            You can go to a specific URL by answering with the following JSON format:
            {"url": "url goes here"}

            You can click links on the website by referencing the ID before the component in the text representation, by answering in the following JSON format:
            {"click": "ID"}

            You can fill in text boxes by referencing the ID before the component in the text representation, by answering in the following JSON format:
            {"input": {"select": "ID", "type": "Text to type"}}

            Don't include the #, @, or $ in the ID when you are answering with the JSON format.

            The IDs are always integer values.

            You can press any key on the keyboard by answering with the following JSON format:
            {"keyboard": "key"}
            make sure your input for "key" works for the page.keyboard.press method from python playwright.

            You can go back, go forward, or reload the page by answering with the following JSON format:
            {"navigation": "back"}
            {"navigation": "forward"}
            {"navigation": "reload"}
            
            Once you are on a URL and you have found the answer to the user's question, you can answer with a regular message.

            Use google search by set a sub-page like 'https://google.com/search?q=search
        """
        self.messages = [
            {"role": "system", "content": self.instructions},
        ]
        self.page = page

    def image_b64(self, image):
        with open(image, "rb") as f:
            return b64encode(f.read()).decode("utf-8")

    async def process_page(self):
        try:
            print("Getting text...")
            page_text, tag_to_xpath = await tarsier.page_to_text(
                self.page, tag_text_elements=True
            )
            print("Taking screenshot...")
            await self.page.screenshot(path="screenshot.jpg", full_page=True)
        except Exception as e:
            print(e)
            return

        self.base64_image = self.image_b64("screenshot.jpg")
        self.tag_to_xpath = tag_to_xpath
        self.page_text = page_text

    def extract_json(self, message):
        json_regex = r"\{.*?\}(?=\s|$)"
        matches = re.findall(json_regex, message, re.DOTALL)

        if matches:
            try:
                json_data = json.loads(matches[0])
                return json_data
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return None
        else:
            print("No JSON found in the message")
            return None

    async def chat(self, input):
        self.messages.append(
            {
                "role": "user",
                "content": input,
            }
        )
        print("User:", input)

        while True:
            if self.url:
                try:
                    await self.page.goto(self.url)
                    # await self.page.wait_for_load_state("networkidle")
                    await self.page.wait_for_timeout(5000)
                except:
                    pass
                print(f"Crawling {self.url}")
                await self.process_page()
                self.url = None

            if self.base64_image:
                print(self.page_text)
                self.messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{self.base64_image}"
                                },
                            },
                            {
                                "type": "text",
                                "text": f"""Here's the screenshot of the website you are on right now.
                                \n{self.instructions}\n
                                Here's the text representation of the website:
                                \n{self.page_text}
                                """,
                            },
                        ],
                    }
                )

                self.base64_image = None

            for attempt in range(3):
                try:
                    response = model.chat.completions.create(
                        model="gpt-4-vision-preview",
                        messages=self.messages,
                        max_tokens=1024,
                    )
                    break
                except openai.RateLimitError as e:
                    print(
                        f"Rate limit exceeded, attempt {attempt + 1} of {3}. Retrying in {60} seconds..."
                    )
                    self.messages = [self.messages[0]] + self.messages[:-1]
                    time.sleep(60)

            if not response:
                raise Exception("API call failed after retrying")

            message = response.choices[0].message
            message_text = message.content

            self.messages.append(
                {
                    "role": "assistant",
                    "content": message_text,
                }
            )

            print("Assistant:", message_text)

            if '{"click":' in message_text:
                click_data = self.extract_json(message_text)
                id = int(click_data["click"])
                elements = await self.page.query_selector_all(self.tag_to_xpath[id])
                if elements:
                    await elements[0].click()
                    try:
                        # await self.page.wait_for_load_state("networkidle")
                        await self.page.wait_for_timeout(5000)
                    except:
                        pass
                await self.process_page()
                continue
            elif '{"url":' in message_text:
                url_data = self.extract_json(message_text)
                self.url = url_data["url"]
                continue
            elif '{"input": {' in message_text:
                input_data = json.loads(message_text)
                id = int(input_data["input"]["select"])
                text_to_type = input_data["input"]["type"]
                elements = await self.page.query_selector_all(self.tag_to_xpath[id])
                if elements:
                    await elements[0].type(text_to_type)
                await self.process_page()
                continue
            elif '{"keyboard":' in message_text:
                keyboard_data = self.extract_json(message_text)
                key = keyboard_data["keyboard"]
                await self.page.keyboard.press(key)
                try:
                    # await self.page.wait_for_load_state("networkidle")
                    await self.page.wait_for_timeout(5000)
                except:
                    pass
                await self.process_page()
                continue
            elif '{"navigation":' in message_text:
                navigation_data = self.extract_json(message_text)
                navigation = navigation_data["navigation"]
                if navigation == "back":
                    await self.page.go_back()
                elif navigation == "forward":
                    await self.page.go_forward()
                elif navigation == "reload":
                    await self.page.reload()
                await self.process_page()
                continue
            return message_text


async def main():
    async with async_playwright() as p:
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

        ## system

        ## user: go to linkedin
        ## assistant: url
        ## user: heres the screenshot
        ## assistant: im on linkedin

        ## user: put software engineer in search bar
        ## assistant: type
        ## user: heres the screenshot
        ## assistant: i have typed

        ## user: press enter on keyboard
        ## assistant: keyboard press
        ## user: heres the screenshot
        ## assistant: i have pressed enter

        # await agent.chat("go to linkedin")
        # await agent.chat("put software engineer in search bar")
        # await agent.chat("press enter on keyboard")
        # await agent.chat("click 'See all people results' near the middle of the page, if it's not there click 'People' near the top of the page")

        # await agent.chat("go to https://www.linkedin.com/search/results/people/?keywords=software%20engineer&origin=SWITCH_SEARCH_VERTICAL&sid=A~y")
        # await agent.chat("click the first person")
        await agent.chat(
            "go to https://www.linkedin.com/in/aram-harutyunyan-49909314a/"
        )
        await agent.chat("click connect")
        await agent.chat("click add a note")
        await agent.chat("type 'Hi, I'd like to connect with you on LinkedIn'")

        # while True:
        #     content = input("You: ")
        #     await call_openai_api_with_retry(agent.chat, content)


asyncio.run(main())
