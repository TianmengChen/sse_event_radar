from abc import ABC, abstractmethod


class BaseNotifier(ABC):
    @abstractmethod
    def send_text(self, title: str, text: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def send_markdown(self, title: str, markdown: str) -> bool:
        raise NotImplementedError