import pytesseract
from PIL import Image
from browser_session import BrowserSession

class UITool:
    def __init__(self, headless=True):
        self.session = None
        self.headless = headless

    def start(self, url: str):
        self.session = BrowserSession(url, headless=self.headless)
        return "Browser started and navigated to " + url

    def screenshot(self, path: str = "page.png"):
        self.session.screenshot(path, full_page=True)
        return path

    def locate_text(self, image_path: str, text: str = "Home"):
        # Run Tesseract OCR to find word‐bounding boxes
        img = Image.open(image_path)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        for i, w in enumerate(data['text']):
            if w.strip().lower() == text.lower():
                x = data['left'][i]
                y = data['top'][i]
                w_ = data['width'][i]
                h_ = data['height'][i]
                # return center of the box
                return (x + w_//2, y + h_//2)
        raise ValueError(f"'{text}' not found on page")

    def click_at(self, x: int, y: int):
        self.session.mouse_click(x, y)
        return f"Clicked at ({x},{y})"

    def close(self):
        self.session.close()
        return "Browser closed"