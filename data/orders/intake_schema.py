from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


IntakeMode = Literal["draft", "submit"]


class IntakePayload(BaseModel):
    mode: IntakeMode = "submit"
    candidate_score: Optional[int] = Field(default=None, ge=0, le=1000)
    candidate_rank: Optional[int] = Field(default=None, ge=0)
    candidate_subjects: list[str] = Field(default_factory=list)
    candidate_interests: Optional[str] = None
    guardian_notes: Optional[str] = None

    @model_validator(mode="after")
    def _validate_submit_payload(self) -> "IntakePayload":
        if self.mode == "submit":
            if self.candidate_score is None:
                raise ValueError("candidate_score 为提交必填项")
            if self.candidate_rank is None:
                raise ValueError("candidate_rank 为提交必填项")
            if not self.candidate_subjects:
                raise ValueError("candidate_subjects 为提交必填项")
        return self


__all__ = ["IntakePayload", "IntakeMode"]
