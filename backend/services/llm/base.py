from abc import ABC, abstractmethod

from backend.schemas.search import SearchIntent


class LLMProvider(ABC):

    @abstractmethod
    def extract_search_intent(self, message: str) -> SearchIntent:
        pass