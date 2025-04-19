# browser_session.py
from playwright.sync_api import sync_playwright, Page, Locator
import time

class BrowserSession:
    def __init__(self, link: str, headless: bool = True):
        """
        Initialize Playwright, launch the browser, create a context and page,
        and navigate to the given link.

        :param link: URL to open
        :param headless: whether to run browser in headless mode
        """
        self.link = link
        # Start Playwright
        self._playwright = sync_playwright().start()
        # Launch Chromium (you can also use firefox or webkit)
        self.browser = self._playwright.chromium.launch(headless=headless)
        # New browser context (isolated session)
        self.context = self.browser.new_context()
        # New page
        self.page = self.context.new_page()

        # Navigate
        self.page.goto(self.link)



    #----------------------------screenshots-------------------------

    def screenshot(self, path: str, full_page: bool = False):
        """
        Capture a screenshot of the current viewport or full page.

        :param path: File path to save the screenshot
        :param full_page: Whether to capture the entire scrollable page
        """
        self.page.screenshot(path=path, full_page=full_page)

    def screenshot_buffer(self, full_page: bool = False) -> bytes:
        """
        Capture a screenshot into a bytes buffer (PNG).

        :param full_page: Whether to capture the entire scrollable page
        :return: PNG image data as bytes
        """
        return self.page.screenshot(full_page=full_page)

    def screenshot_element(self, selector: str, path: str):
        """
        Capture a screenshot of a single element matching the selector.

        :param selector: CSS or role-based selector for the element
        :param path: File path to save the element screenshot
        """
        element = self.page.locator(selector)
        element.screenshot(path=path)

    def screenshot_locator(self, locator: Locator, path: str):
        """
        Capture a screenshot of a Locator instance.

        :param locator: Playwright Locator object
        :param path: File path to save the screenshot
        """
        locator.screenshot(path=path)

    def screenshot_clip(self, path: str, x: int, y: int, width: int, height: int):
        """
        Capture a screenshot of a clipped region of the page.

        :param path: File path to save the screenshot
        :param x: X-coordinate of the clipping rectangle
        :param y: Y-coordinate of the clipping rectangle
        :param width: Width of the clipping rectangle
        :param height: Height of the clipping rectangle
        """
        clip = {"x": x, "y": y, "width": width, "height": height}
        self.page.screenshot(path=path, clip=clip)

    
    #--------------------------------Clicks------------------------

    def scroll_into_view(self, selector: str):
        """
        Scroll the element matching selector into view.
        """
        self.page.locator(selector).scroll_into_view_if_needed()

    def click(self,
              selector: str,
              force: bool = False,
              position: dict = None,
              modifiers: list = None,
              button: str = "left",
              timeout: int = None):
        """
        Scrolls to and clicks an element by CSS selector.

        :param selector: CSS selector of the element
        :param force: bypass actionability checks
        :param position: {'x':int,'y':int} within element
        :param modifiers: list of keys, e.g. ['Shift']
        :param button: 'left', 'right', or 'middle'
        :param timeout: maximum wait time in ms
        """
        loc = self.page.locator(selector)
        loc.scroll_into_view_if_needed()
        loc.click(force=force, position=position, modifiers=modifiers, button=button, timeout=timeout)

    def click_by_role(self, role: str, name: str, **kwargs):
        """
        Click an element found by ARIA role and name.
        """
        loc = self.page.get_by_role(role, name=name)
        loc.scroll_into_view_if_needed()
        loc.click(**kwargs)

    def click_by_text(self, text: str, **kwargs):
        """
        Click an element containing the given text.
        """
        loc = self.page.get_by_text(text)
        loc.scroll_into_view_if_needed()
        loc.click(**kwargs)

    def dispatch_click(self, selector: str):
        """
        Programmatically trigger a click event on the element.
        """
        self.page.locator(selector).dispatch_event('click')


    # --------------------Mouse Movement & Actions --------------------
    def mouse_move(self, x: float, y: float, steps: int = 1):
        """
        Move mouse to (x, y) in viewport coordinates.
        """
        self.page.mouse.move(x, y, steps=steps)
        # Fallback using pyautogui if needed:
        # import pyautogui
        # pyautogui.moveTo(x, y)

    def mouse_click(self, x: float, y: float, button: str = 'left', click_count: int = 1, delay: float = 0):
        """
        Click at (x, y) with mouse button.
        """
        self.page.mouse.click(x, y, button=button, click_count=click_count, delay=delay)
        # Fallback using pyautogui:
        # import pyautogui
        # pyautogui.click(x, y, clicks=click_count, interval=delay/1000 if delay else 0, button=button)

    def mouse_dblclick(self, x: float, y: float, button: str = 'left', delay: float = 0):
        """
        Double click at (x, y) coordinates.
        """
        self.page.mouse.dblclick(x, y, button=button, delay=delay)
        # Fallback using pyautogui:
        # import pyautogui
        # pyautogui.doubleClick(x, y, interval=delay/1000 if delay else 0, button=button)

    def mouse_down(self, button: str = 'left', click_count: int = 1):
        """
        Dispatch a mousedown event at current mouse position.
        """
        self.page.mouse.down(button=button, click_count=click_count)
        # Fallback using pyautogui:
        # import pyautogui
        # pyautogui.mouseDown(button=button)

    def mouse_up(self, button: str = 'left', click_count: int = 1):
        """
        Dispatch a mouseup event at current mouse position.
        """
        self.page.mouse.up(button=button, click_count=click_count)
        # Fallback using pyautogui:
        # import pyautogui
        # pyautogui.mouseUp(button=button)

    def mouse_wheel(self, delta_x: float, delta_y: float):
        """
        Dispatch a wheel event to scroll.
        """
        self.page.mouse.wheel(delta_x, delta_y)
        # Fallback using pyautogui:
        # import pyautogui
        # pyautogui.scroll(delta_y)


    #------------terminate----------------------------------

    def close(self):
        """Cleanly close page, context, browser and stop Playwright."""
        try:
            self.page.close()
            self.context.close()
            self.browser.close()
        finally:
            self._playwright.stop()

    


# Example usage
if __name__ == "__main__":
    session = BrowserSession("https://playwright.dev/", headless=True)
    print("Page title is:", session.page.title())
    session.screenshot("./images/screenshot.jpg")
    # ... do whatever actions/assertions you like, e.g.:
    # session.page.get_by_role("link", name="Get started").click()
    time.sleep(3)
    session.close()
