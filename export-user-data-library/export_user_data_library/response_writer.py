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
        if type(result) == dict:
            print(f"[out] {json.dumps(result)}")
        else:
            print(f"[out] {result}")


class TesResponseWriter(ResponseWriter):
    """
    TODO: Add TES support.
    """

    def write(self, result) -> None:
        raise NotImplementedError
