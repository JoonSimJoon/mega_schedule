from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
from typing import List
from database import get_db, User, Schedule, Class, AssignmentStatus
from auth import require_desk
from models import (
    ClassCreate, ClassResponse,
    AvailableTeacherResponse,
    TeacherWorkTimeResponse
)

router = APIRouter(prefix="/api/desk", tags=["desk"])


@router.get("/teachers/available", response_model=List[AvailableTeacherResponse])
async def get_available_teachers(
    start_time: datetime = None,
    end_time: datetime = None,
    current_user: User = Depends(require_desk),
    db: AsyncSession = Depends(get_db)
):
    """학원 데스크 - 선생이 가능한 시간 조회 (학생 배정용)"""
    # 모든 선생 조회
    teachers_result = await db.execute(
        select(User).where(User.role == "teacher")
    )
    teachers = teachers_result.scalars().all()
    
    available_teachers = []
    
    for teacher in teachers:
        # 해당 선생의 사용 가능한 스케줄 조회
        query = select(Schedule).where(
            and_(
                Schedule.teacher_id == teacher.id,
                Schedule.is_available == True
            )
        )
        
        if start_time:
            query = query.where(Schedule.start_time >= start_time)
        if end_time:
            query = query.where(Schedule.end_time <= end_time)
        
        query = query.order_by(Schedule.start_time)
        
        schedules_result = await db.execute(query)
        schedules = schedules_result.scalars().all()
        
        if schedules:
            available_teachers.append(
                AvailableTeacherResponse(
                    teacher_id=teacher.id,
                    teacher_name=teacher.name,
                    available_schedules=list(schedules)
                )
            )
    
    return available_teachers


@router.post("/classes", response_model=ClassResponse)
async def assign_student(
    class_data: ClassCreate,
    current_user: User = Depends(require_desk),
    db: AsyncSession = Depends(get_db)
):
    """학원 데스크 - 학생 배정"""
    # 스케줄 확인
    schedule_result = await db.execute(
        select(Schedule).where(Schedule.id == class_data.schedule_id)
    )
    schedule = schedule_result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    if not schedule.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule is not available"
        )
    
    # 이미 배정된 수업이 있는지 확인
    existing_class = await db.execute(
        select(Class).where(
            and_(
                Class.schedule_id == class_data.schedule_id,
                Class.status == AssignmentStatus.ACCEPTED.value
            )
        )
    )
    if existing_class.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule already has an accepted class"
        )
    
    # 수업 생성
    class_obj = Class(
        student_name=class_data.student_name,
        teacher_id=schedule.teacher_id,
        schedule_id=class_data.schedule_id,
        status=AssignmentStatus.PENDING.value,
        created_by=current_user.id
    )
    
    db.add(class_obj)
    await db.commit()
    await db.refresh(class_obj)
    
    return class_obj


@router.get("/teachers/schedules", response_model=List[TeacherWorkTimeResponse])
async def get_all_teacher_schedules(
    year: int = None,
    month: int = None,
    teacher_id: int = None,
    current_user: User = Depends(require_desk),
    db: AsyncSession = Depends(get_db)
):
    """학원 데스크 - 선생들 근무 일정 및 시간 조회"""
    now = datetime.utcnow()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    # 해당 월의 시작일과 종료일
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # 선생 조회
    teachers_query = select(User).where(User.role == "teacher")
    if teacher_id:
        teachers_query = teachers_query.where(User.id == teacher_id)
    
    teachers_result = await db.execute(teachers_query)
    teachers = teachers_result.scalars().all()
    
    results = []
    
    for teacher in teachers:
        # 해당 선생의 수락된 수업 조회
        result = await db.execute(
            select(Class, Schedule)
            .join(Schedule, Class.schedule_id == Schedule.id)
            .where(
                and_(
                    Class.teacher_id == teacher.id,
                    Class.status == AssignmentStatus.ACCEPTED.value,
                    Schedule.start_time >= start_date,
                    Schedule.start_time < end_date
                )
            )
        )
        classes_with_schedules = result.all()
        
        # 총 근무 시간 계산
        total_hours = 0.0
        schedules_list = []
        
        for class_obj, schedule in classes_with_schedules:
            duration = (schedule.end_time - schedule.start_time).total_seconds() / 3600
            total_hours += duration
            schedules_list.append(schedule)
        
        results.append(
            TeacherWorkTimeResponse(
                teacher_id=teacher.id,
                teacher_name=teacher.name,
                total_hours=round(total_hours, 2),
                classes_count=len(classes_with_schedules),
                schedules=schedules_list
            )
        )
    
    return results


@router.get("/classes", response_model=List[ClassResponse])
async def get_all_classes(
    status_filter: str = None,
    teacher_id: int = None,
    current_user: User = Depends(require_desk),
    db: AsyncSession = Depends(get_db)
):
    """학원 데스크 - 모든 수업 조회"""
    query = select(Class)
    
    if status_filter:
        query = query.where(Class.status == status_filter)
    if teacher_id:
        query = query.where(Class.teacher_id == teacher_id)
    
    query = query.order_by(Class.created_at.desc())
    
    result = await db.execute(query)
    classes = result.scalars().all()
    return classes


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: str,
    current_user: User = Depends(require_desk),
    db: AsyncSession = Depends(get_db)
):
    """학원 데스크 - 유저 역할 변경"""
    if new_role not in ["teacher", "desk"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'teacher' or 'desk'"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = new_role
    await db.commit()
    await db.refresh(user)
    
    return {"message": "User role updated successfully", "user": user}

