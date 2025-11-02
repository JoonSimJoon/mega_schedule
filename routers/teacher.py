from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
from typing import List
from database import get_db, User, Schedule, Class, AssignmentStatus
from auth import require_teacher
from models import (
    ScheduleCreate, ScheduleResponse,
    ClassResponse, ClassAcceptRequest,
    TeacherWorkTimeResponse
)

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db)
):
    """선생 - 본인 일정 등록"""
    if schedule_data.start_time >= schedule_data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time"
        )
    
    schedule = Schedule(
        teacher_id=current_user.id,
        start_time=schedule_data.start_time,
        end_time=schedule_data.end_time,
        is_available=schedule_data.is_available
    )
    
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    
    return schedule


@router.get("/schedules", response_model=List[ScheduleResponse])
async def get_my_schedules(
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db)
):
    """선생 - 본인 일정 조회"""
    result = await db.execute(
        select(Schedule)
        .where(Schedule.teacher_id == current_user.id)
        .order_by(Schedule.start_time)
    )
    schedules = result.scalars().all()
    return schedules


@router.get("/classes", response_model=List[ClassResponse])
async def get_my_classes(
    status_filter: str = None,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db)
):
    """선생 - 배정된 수업 확인"""
    query = select(Class).where(Class.teacher_id == current_user.id)
    
    if status_filter:
        query = query.where(Class.status == status_filter)
    
    query = query.order_by(Class.created_at.desc())
    
    result = await db.execute(query)
    classes = result.scalars().all()
    return classes


@router.get("/classes/pending", response_model=List[ClassResponse])
async def get_pending_classes(
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db)
):
    """선생 - 대기 중 수업 확인"""
    result = await db.execute(
        select(Class)
        .where(
            and_(
                Class.teacher_id == current_user.id,
                Class.status == AssignmentStatus.PENDING.value
            )
        )
        .order_by(Class.created_at)
    )
    classes = result.scalars().all()
    return classes


@router.post("/classes/{class_id}/accept", response_model=ClassResponse)
async def accept_class(
    class_id: int,
    request: ClassAcceptRequest,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db)
):
    """선생 - 대기 중 수업 수락/거절"""
    result = await db.execute(
        select(Class)
        .where(
            and_(
                Class.id == class_id,
                Class.teacher_id == current_user.id,
                Class.status == AssignmentStatus.PENDING.value
            )
        )
    )
    class_obj = result.scalar_one_or_none()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or not pending"
        )
    
    if request.accept:
        class_obj.status = AssignmentStatus.ACCEPTED.value
        class_obj.accepted_at = datetime.utcnow()
        
        # 스케줄을 사용 불가능으로 변경
        schedule_result = await db.execute(
            select(Schedule).where(Schedule.id == class_obj.schedule_id)
        )
        schedule = schedule_result.scalar_one()
        schedule.is_available = False
    else:
        class_obj.status = AssignmentStatus.REJECTED.value
    
    await db.commit()
    await db.refresh(class_obj)
    
    return class_obj


@router.get("/worktime", response_model=TeacherWorkTimeResponse)
async def get_monthly_worktime(
    year: int = None,
    month: int = None,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db)
):
    """선생 - 이번달 근무시간 확인 (정산)"""
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
    
    # 수락된 수업 조회
    result = await db.execute(
        select(Class, Schedule)
        .join(Schedule, Class.schedule_id == Schedule.id)
        .where(
            and_(
                Class.teacher_id == current_user.id,
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
    
    return TeacherWorkTimeResponse(
        teacher_id=current_user.id,
        teacher_name=current_user.name,
        total_hours=round(total_hours, 2),
        classes_count=len(classes_with_schedules),
        schedules=schedules_list
    )


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db)
):
    """선생 - 일정 삭제"""
    result = await db.execute(
        select(Schedule).where(
            and_(
                Schedule.id == schedule_id,
                Schedule.teacher_id == current_user.id
            )
        )
    )
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    # 수업이 배정된 일정은 삭제 불가
    class_result = await db.execute(
        select(Class).where(Class.schedule_id == schedule_id)
    )
    if class_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete schedule with assigned classes"
        )
    
    db.delete(schedule)
    await db.commit()
    
    return {"message": "Schedule deleted successfully"}

