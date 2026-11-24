from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from src.constants.domain import Basis, Branch

TicketCode = Annotated[str, StringConstraints(pattern=r'^[A-Z0-9][A-Z0-9-]{2,31}$')]
PlanKey = Annotated[str, StringConstraints(pattern=r'^[A-Z0-9][A-Z0-9-]{2,31}$')]


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Login(Input):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class TicketFields(Input):
    branch: Branch
    worked_on: date
    ribs: int = Field(ge=0, le=12)
    fabric: int = Field(ge=0, le=12)
    mechanism: int = Field(ge=0, le=1)
    minutes: int = Field(ge=1, le=480)
    note: str = Field(default='', max_length=180)


class NewTicket(TicketFields):
    code: TicketCode


class TicketEdit(TicketFields):
    revision: int = Field(ge=1)


class PlanFields(Input):
    label: str = Field(min_length=1, max_length=100)
    focus_branch: Branch
    control_branch: Branch
    coefficient_ref: Basis
    date_from: date
    date_to: date
    min_samples: int = Field(ge=8, le=500)

    @model_validator(mode='after')
    def validate_comparison(self):
        if self.focus_branch == self.control_branch:
            raise ValueError('比较网点和对照网点必须不同')
        if not 0 <= (self.date_to - self.date_from).days <= 365:
            raise ValueError('日期须按先后顺序填写，窗口最多 366 天')
        return self


class NewPlan(PlanFields):
    plan_key: PlanKey


class PlanRevision(PlanFields):
    base_version: int = Field(ge=1)


class StartRun(Input):
    plan_id: int = Field(ge=1)


class DraftText(Input):
    action_text: str = Field(min_length=5, max_length=1000)
