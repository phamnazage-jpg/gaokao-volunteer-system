from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


IntakeMode = Literal["draft", "submit"]


class IntakePayload(BaseModel):
    mode: IntakeMode = "submit"
    candidate_score: Optional[int] = Field(default=None, ge=0, le=1000)
    candidate_rank: Optional[int] = Field(default=None, ge=0)
    candidate_subjects: list[str] = Field(default_factory=list, max_length=6)
    candidate_interests: Optional[str] = Field(default=None, max_length=200)
    target_cities: list[str] = Field(default_factory=list, max_length=5)
    target_majors: list[str] = Field(default_factory=list, max_length=10)
    university_preferences: Optional[str] = Field(default=None, max_length=500)
    existing_plan_summary: Optional[str] = Field(default=None, max_length=1000)
    guardian_notes: Optional[str] = Field(default=None, max_length=1000)
    consent_version: Optional[str] = None
    consent_scope: Optional[str] = None
    privacy_accepted: bool = False
    service_terms_accepted: bool = False
    guardian_confirmed: bool = False

    @model_validator(mode="after")
    def _validate_submit_payload(self) -> "IntakePayload":
        if self.mode == "submit":
            if self.candidate_score is None:
                raise ValueError("candidate_score 为提交必填项")
            if self.candidate_rank is None:
                raise ValueError("candidate_rank 为提交必填项")
            if not self.candidate_subjects:
                raise ValueError("candidate_subjects 为提交必填项")
            if not self.consent_version:
                raise ValueError("consent_version 为提交必填项")
            if not self.consent_scope:
                raise ValueError("consent_scope 为提交必填项")
            if not self.privacy_accepted:
                raise ValueError("privacy_accepted 为提交必填项")
            if not self.service_terms_accepted:
                raise ValueError("service_terms_accepted 为提交必填项")
            if not self.guardian_confirmed:
                raise ValueError("guardian_confirmed 为提交必填项")
            if not (
                self.candidate_interests
                or self.target_cities
                or self.target_majors
                or self.university_preferences
            ):
                raise ValueError("至少填写一个偏好与目标字段")
        return self


__all__ = ["IntakePayload", "IntakeMode"]
