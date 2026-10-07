from abc import ABC, abstractmethod
from app.perception.types import NetworkFrame
from app.perception.models import CVResult

class CVProcessor(ABC):
    """
    Generic contract for Computer Vision processing algorithms.
    Decouples specific model implementations (like YOLO) from the 
    AEROSAR Incident Engine pipeline.
    """
    
    @abstractmethod
    def process(self, frame: NetworkFrame) -> CVResult:
        """
        Processes a single frame and returns a strongly-typed CVResult.
        
        Args:
            frame: A decoded NetworkFrame containing raw pixels and telemetry.
            
        Returns:
            A structured CVResult with 0 or more DetectionResult objects.
            If a non-fatal error occurs, it should return a CVResult with `error` populated.
            
        Raises:
            Should not raise raw exceptions that crash the PerceptionWorker.
            Exceptions must be caught internally and translated to an error CVResult.
        """
        pass
