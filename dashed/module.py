import dataclasses
from typing import Any, Dict, List
import typing


@dataclasses.dataclass
class DashedCommand:
    name: str
    description: str
    fn: Any

    def get_args(self) -> Dict[str, type]:
        return {k: v for k, v in list(typing.get_type_hints(self.fn).items())[1:]}


@dataclasses.dataclass
class DashedModule:
    name: str
    commands: List[DashedCommand]
