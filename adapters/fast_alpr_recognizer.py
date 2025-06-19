from fast_alpr import ALPR
from ports.plate_recognizer import PlateRecognizer

class FastALPRRecognizer(PlateRecognizer):
    def __init__(self):
        print("[INFO] Cargando modelo fast-alpr desde archivos locales...")
        self.alpr = ALPR(
            detector_model="yolo-v9-t-384-license-plate-end2end", 
            ocr_model="global-plates-mobile-vit-v2-model"         
        )

    def recognize(self, image_path: str) -> str:
        results = self.alpr.predict(image_path)
        if results:
            return results[0].ocr.text
        return "No plate detected"
