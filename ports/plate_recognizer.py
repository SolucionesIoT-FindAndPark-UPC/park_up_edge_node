from abc import ABC, abstractmethod

class PlateRecognizer(ABC):
    @abstractmethod
    def recognize(self, image):
        pass