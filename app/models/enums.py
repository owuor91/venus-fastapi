import enum


class GenderEnum(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class PlanEnum(str, enum.Enum):
    MONTHLY = "MONTHLY"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    ANNUAL = "ANNUAL"
    VIP = "VIP"
    TEST = "TEST"
