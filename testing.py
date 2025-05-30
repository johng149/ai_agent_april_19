# %%
import random
from playwright.sync_api import sync_playwright, Page, Locator
import time
import moondream as md
from PIL import Image
from io import BytesIO
import pyautogui

# %%
class moondream:
    def __init__(self, api_key=None,  endpoint=None):
        if api_key:
            self.model = md.vl(api_key=api_key)

    def point_buttons(self, image, prompt):

        # Locate objects (e.g., "person", "car", "face", etc.)
        result = self.model.point(image, prompt)
        points = result["points"]
        print(result)
        print(f"Found {len(points)} buttons")
        return points

    def img_summary(self, image, cap_length="short"):
        result = self.model.caption(image, length=cap_length)
        caption = result["caption"]
        return caption

# %%
class PlaywrightClient:
    def __init__(self, starting_url, moondream: moondream, headless = False):
        self.link = starting_url
        # Start Playwright
        self._playwright = sync_playwright().start()
        # Launch Chromium (you can also use firefox or webkit)
        self.browser = self._playwright.chromium.launch(headless=headless, args=["--start-maximized"])
        # New browser context (isolated session)
        self.context = self.browser.new_context(no_viewport=True)
        # New page
        self.page = self.context.new_page()
        self.mdinstance = moondream
        # Navigate
        self.page.goto(self.link)
    
    # def mouse_move(self, x: float, y: float, steps: int = 1):
    #     """
    #     Move mouse to (x, y) in viewport coordinates.
    #     """
    #     self.page.mouse.move(x, y, steps=steps)
    #     # Fallback using pyautogui if needed:
    #     # import pyautogui
    #     # pyautogui.moveTo(x, y)

    def click(self, coordinates: tuple[float, float]) -> bool:
        """
        Clicking on a web page, after clicking, will automatically wait for all
        elements to load.

        Args:
            coordinates: A tuple containing the x and y coordinates to click.

        Returns:
             A boolean indicating whether the click was successful.
        """
        # self.page.mouse.move(coordinates[0], coordinates[1], steps=1)
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(x=screen_width * coordinates[0], y=screen_height * coordinates[1] + 10)
        # self.page.mouse.click(screen_width * coordinates[0], screen_height * coordinates[1], button='left', click_count=1, delay=0)
    
    def key_stroke(self, input) -> bool:
        self.page.keyboard.type(input)
        return True

    def describe(self) -> str:
        """
         Description of the current web page.

        Returns:
            A string representing the caption.
        """
        page_screenshot = self.page.screenshot(full_page=False, type="jpeg")
        # Convert the screenshot bytes to a PIL Image
        image = Image.open(BytesIO(page_screenshot))
        return self.mdinstance.img_summary(image)
        
    
    def find_element(self, description: str):
        page_screenshot = self.page.screenshot(full_page=False, type="jpeg")
        # Convert the screenshot bytes to a PIL Image
        image = Image.open(BytesIO(page_screenshot))
        return self.mdinstance.point_buttons(image, description)
        

# %%
class TheoryStatus:
    def __init__(self):
        self.status = None

    def theory_status(self, success: bool) -> bool:
        """
        Log the theory status. This should be used at the very end.

        Args:
            success: A boolean indicating whether the theory was successful.
        Returns:
            A boolean indicating whether the logging was successful.
        """
        self.status = success
        return True

# %%
schemas = [
    {
        "name": "find_element",
        "description": "Find an element on a web page.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "A description of the element to find.",
                }
            },
            "required": ["description"],
        },
    },
    {
        "name": "key_stroke",
        "description": "Inputs given string as keystrokes",
        "parameters": {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "The string to input"
                }
            },
            "required": ["input"]
        }
    },
    {
        "name": "click",
        "description": "Clicking on a web page, after clicking, will automatically wait for all elements to load.",
        "parameters": {
            "type": "object",
            "properties": {
                "coordinates": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "A tuple containing the x and y coordinates to click.",
                }
            },
            "required": ["coordinates"],
        },
    },
    {
        "name": "describe",
        "description": "Description of the current web page.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "theory_status",
        "description": 'Log the theory status. This should be used at the very end.',
        "parameters": {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": 'A boolean indicating whether the theory was successful.',
                }
            },
            'required': ['success'],
        },
    },
]

# %%
ts = TheoryStatus()
moondreammodel = moondream(api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlfaWQiOiJhYmIyY2IwMC05MzdiLTQ2MzktODU3MC05MDdkZjBmZGRkMTIiLCJvcmdfaWQiOiJXUDdKU2VucmxzS3N6U1FPbWgwYUphVlRRSUIyVmNzZyIsImlhdCI6MTc0NTA4Njg3NCwidmVyIjoxfQ.P6L5CW0b8AaXjTbg9XgoVQVFyXkJiToXXujEoGoe34w")
starting_url = "https://duckduckgo.com/"
# starting_url = "https://replit.com/"
playwright = PlaywrightClient(starting_url=starting_url, moondream=moondreammodel)
tools = [
    playwright.find_element,
    playwright.key_stroke,
    playwright.click,
    playwright.describe,
    ts.theory_status,
]

# %%
key = "AIzaSyAuSJjugrpkM94g-sb-IlQ88lSTgEGAG08"

# %%
from gemini import GeminiAgent


# %%
agent = GeminiAgent(tools, schemas, key)

# %%
message = """
Theory: Find the "Set as Default Search" button. Click it. Verify that a window opens up.
Start executing test using tools.
"""

message = """
Theory: Find the "Set as Default Search" button. Click it. Then click the "Got it" button.
Verify that there is a search bar.
Start executing test using tools
"""

# message = """
# Theory: Click the pricing button
# Start executing test using tools.
# """

# %%
agent.reset()

# %%
res = agent.run(message, recursion=8)

# %%
res

# %%
res.text

# %%
agent.halt

# %%
print(agent.contents)

# %%
print(ts.status)

# %%



