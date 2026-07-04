"""Objective components — Doc 07."""

from app.solver.objective.components.f1_workload_balance import F1WorkloadBalance
from app.solver.objective.components.f2_teacher_group_preference import F2TeacherGroupPreference
from app.solver.objective.components.f3_timeslot_preference import F3TimeslotPreference
from app.solver.objective.components.f4_schedule_compactness import F4ScheduleCompactness
from app.solver.objective.components.f5_soft_penalties import F5SoftPenalties
from app.solver.objective.components.f6_room_utilization import F6RoomUtilization

__all__ = [
    "F1WorkloadBalance",
    "F2TeacherGroupPreference",
    "F3TimeslotPreference",
    "F4ScheduleCompactness",
    "F5SoftPenalties",
    "F6RoomUtilization",
]
