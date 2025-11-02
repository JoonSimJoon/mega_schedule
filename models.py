from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str


class UserCreate(UserBase):
    google_id: str


class UserResponse(UserBase):
    id: int
    google_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleBase(BaseModel):
    start_time: datetime
    end_time: datetime
    is_available: bool = True


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleResponse(ScheduleBase):
    id: int
    teacher_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClassBase(BaseModel):
    student_name: str
    schedule_id: int


class ClassCreate(ClassBase):
    pass


class ClassResponse(ClassBase):
    id: int
    teacher_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    accepted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClassAcceptRequest(BaseModel):
    accept: bool  # True: 수락, False: 거절


class TeacherWorkTimeResponse(BaseModel):
    teacher_id: int
    teacher_name: str
    total_hours: float
    classes_count: int
    schedules: list[ScheduleResponse]


class AvailableTeacherResponse(BaseModel):
    teacher_id: int
    teacher_name: str
    available_schedules: list[ScheduleResponse]

