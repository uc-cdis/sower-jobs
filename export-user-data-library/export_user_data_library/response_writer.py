import json
from abc import abstractmethod, ABC


class ResponseWriter(ABC):
    @abstractmethod
    def write(self, result) -> None:
        raise NotImplementedError


class SowerResponseWriter(ResponseWriter):
    """
    Response writer for sower.
    """

    def write(self, result) -> None:
        print(f"[out] {json.dumps(result)}")


class TesResponseWriter(ResponseWriter):
    """
    TODO: Add TES support.
    """

    def write(self, result) -> None:
        raise NotImplementedError
