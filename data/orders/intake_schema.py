from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


IntakeMode = Literal["draft", "submit"]


class IntakePayload(BaseModel):
    mode: IntakeMode = "submit"
    candidate_province: Optional[str] = Field(default=None, max_length=32)
    candidate_score: Optional[int] = Field(default=None, ge=0, le=1000)
    candidate_rank: Optional[int] = Field(default=None, ge=0)
    candidate_subjects: list[str] = Field(default_factory=list, max_length=6)
    candidate_interests: Optional[str] = Field(default=None, max_length=200)
    target_cities: list[str] = Field(default_factory=list, max_length=5)
    target_majors: list[str] = Field(default_factory=list, max_length=10)
    university_preferences: Optional[str] = Field(default=None, max_length=500)
    school_region_preferences: list[str] = Field(default_factory=list, max_length=10)
    school_preference_types: list[str] = Field(default_factory=list, max_length=10)
    target_schools: list[str] = Field(default_factory=list, max_length=10)
    disliked_majors: list[str] = Field(default_factory=list, max_length=10)
    priority_strategy: Optional[str] = Field(default=None, max_length=64)
    graduation_plan: Optional[str] = Field(default=None, max_length=128)
    tuition_preference: Optional[str] = Field(default=None, max_length=128)
    employment_region_preferences: list[str] = Field(default_factory=list, max_length=10)
    family_background: Optional[str] = Field(default=None, max_length=300)
    industry_resources: Optional[str] = Field(default=None, max_length=300)
    extra_notes: Optional[str] = Field(default=None, max_length=1000)
    interest_assessment_type: Optional[str] = Field(default=None, max_length=64)
    interest_assessment_result: Optional[str] = Field(default=None, max_length=200)
    interest_assessment_notes: Optional[str] = Field(default=None, max_length=500)
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
            if not self.candidate_province:
                raise ValueError("candidate_province 为提交必填项")
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
        return self


__all__ = ["IntakePayload", "IntakeMode"]
