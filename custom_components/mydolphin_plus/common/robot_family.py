from enum import StrEnum


class RobotFamily(StrEnum):
    ALL = "all"
    M700 = "M700"

    @staticmethod
    def from_string(text: str | None):
        value = RobotFamily.ALL

        all_options: list[str] = list(RobotFamily)

        for option in all_options:
            item = RobotFamily(option)
            is_match = item.value == text

            if is_match:
                value = item
                break

        return value
