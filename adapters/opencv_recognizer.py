from ports.plate_recognizer import PlateRecognizer
import cv2
import pytesseract
import os

class OpenCVRecognizer(PlateRecognizer):
    def recognize(self, image):
        img = cv2.imread(image)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        text = pytesseract.image_to_string(thresh, config='--psm 7')
        print(f"OCR Text: {text.strip()}")
        return text.strip()
    

