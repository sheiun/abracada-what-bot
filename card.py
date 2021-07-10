from __future__ import annotations

from dataclasses import dataclass
from json import load
from operator import eq, ge, gt, le, lt
from typing import Tuple, Union

PASS = {
    "icon": "⏭️",
    "sticker_id": "CAACAgUAAxkBAAECMzVgfHIPWXCWF7Rp7CekQ4rV_fI6yAACSQIAAi974VdHJthaSiSIex8E",
}


@dataclass
class Card:
    id: str
    icon: str
    name: str
    effect: str
    sticker_id: str

    @classmethod
    def from_id(cls, id: str) -> Card:
        return cls(id, **stones[id])

    def __extract(self, obj: Union[int, str, Card]) -> Tuple[int, int]:
        a = int(self.id)
        if isinstance(obj, int):
            b = obj
        elif isinstance(obj, str):
            b = int(obj)
        else:
            b = int(obj.id)
        return a, b

    def __eq__(self, obj):
        return eq(*self.__extract(obj))

    def __ge__(self, obj):
        return ge(*self.__extract(obj))

    def __gt__(self, obj):
        return gt(*self.__extract(obj))

    def __le__(self, obj):
        return le(*self.__extract(obj))

    def __lt__(self, obj):
        return lt(*self.__extract(obj))

    def short(self):
        return f"{self.icon} ({self.id})"

    def __str__(self) -> str:
        return f"{self.icon} {self.name} ({self.id})"


stones = load(open("stones.json"))
CARDS = [Card.from_id(str(i)) for i in range(1, 9) for _ in range(i)]
assert len(CARDS) == 36

print("[INFO] Cards loaded")
