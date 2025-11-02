# API 엔드포인트 문서

## 인증
모든 API 요청은 `Authorization: Bearer {token}` 헤더에 Google ID 토큰을 포함해야 합니다.

## 공통 API

### GET /api/me
현재 로그인한 유저 정보 조회
- **인증 필요**: 예
- **응답**: UserResponse

### GET /api/health
헬스 체크
- **인증 필요**: 아니오

---

## 선생 (Teacher) API

### POST /api/teacher/schedules
본인 일정 등록
- **인증 필요**: 예 (선생 역할)
- **요청 본문**: ScheduleCreate
- **응답**: ScheduleResponse

### GET /api/teacher/schedules
본인 일정 조회
- **인증 필요**: 예 (선생 역할)
- **응답**: List[ScheduleResponse]

### DELETE /api/teacher/schedules/{schedule_id}
일정 삭제 (수업이 배정되지 않은 일정만 삭제 가능)
- **인증 필요**: 예 (선생 역할)
- **응답**: {"message": "Schedule deleted successfully"}

### GET /api/teacher/classes
배정된 수업 확인
- **인증 필요**: 예 (선생 역할)
- **쿼리 파라미터**: 
  - `status_filter` (optional): 수업 상태 필터 (pending, accepted, rejected)
- **응답**: List[ClassResponse]

### GET /api/teacher/classes/pending
대기 중 수업 확인
- **인증 필요**: 예 (선생 역할)
- **응답**: List[ClassResponse]

### POST /api/teacher/classes/{class_id}/accept
대기 중 수업 수락/거절
- **인증 필요**: 예 (선생 역할)
- **요청 본문**: ClassAcceptRequest
  - `accept`: boolean (true: 수락, false: 거절)
- **응답**: ClassResponse

### GET /api/teacher/worktime
이번달 근무시간 확인 (정산)
- **인증 필요**: 예 (선생 역할)
- **쿼리 파라미터**: 
  - `year` (optional): 년도 (기본값: 현재 년도)
  - `month` (optional): 월 (기본값: 현재 월)
- **응답**: TeacherWorkTimeResponse
  - `teacher_id`: 선생 ID
  - `teacher_name`: 선생 이름
  - `total_hours`: 총 근무 시간 (시간 단위)
  - `classes_count`: 수업 개수
  - `schedules`: 수업 일정 목록

---

## 학원 데스크 (Desk) API

### GET /api/desk/teachers/available
선생이 가능한 시간 조회 (학생 배정용)
- **인증 필요**: 예 (데스크 역할)
- **쿼리 파라미터**: 
  - `start_time` (optional): 시작 시간 필터 (datetime)
  - `end_time` (optional): 종료 시간 필터 (datetime)
- **응답**: List[AvailableTeacherResponse]
  - 각 선생별로 사용 가능한 스케줄 목록

### POST /api/desk/classes
학생 배정
- **인증 필요**: 예 (데스크 역할)
- **요청 본문**: ClassCreate
  - `student_name`: 학생 이름
  - `schedule_id`: 스케줄 ID
- **응답**: ClassResponse

### GET /api/desk/teachers/schedules
선생들 근무 일정 및 시간 조회
- **인증 필요**: 예 (데스크 역할)
- **쿼리 파라미터**: 
  - `year` (optional): 년도 (기본값: 현재 년도)
  - `month` (optional): 월 (기본값: 현재 월)
  - `teacher_id` (optional): 특정 선생만 조회
- **응답**: List[TeacherWorkTimeResponse]

### GET /api/desk/classes
모든 수업 조회
- **인증 필요**: 예 (데스크 역할)
- **쿼리 파라미터**: 
  - `status_filter` (optional): 수업 상태 필터 (pending, accepted, rejected)
  - `teacher_id` (optional): 특정 선생의 수업만 조회
- **응답**: List[ClassResponse]

### PATCH /api/desk/users/{user_id}/role
유저 역할 변경
- **인증 필요**: 예 (데스크 역할)
- **요청 본문**: 
  - `new_role`: "teacher" 또는 "desk"
- **응답**: {"message": "User role updated successfully", "user": User}

---

## 데이터 모델

### ScheduleCreate
```json
{
  "start_time": "2024-01-15T09:00:00Z",
  "end_time": "2024-01-15T10:00:00Z",
  "is_available": true
}
```

### ClassCreate
```json
{
  "student_name": "홍길동",
  "schedule_id": 1
}
```

### ClassAcceptRequest
```json
{
  "accept": true
}
```

