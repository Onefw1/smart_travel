from dataclasses import dataclass, field


@dataclass
class AppError(Exception):
    status: int
    code: str
    message: str
    details: list[dict[str, str]] = field(default_factory=list)
