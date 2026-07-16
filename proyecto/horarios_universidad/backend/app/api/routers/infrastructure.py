"""Infrastructure REST endpoints (buildings, classrooms, resources)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user, require_role
from app.api.dependencies.database import get_uow
from app.api.schemas.base import ApiResponse
from app.api.schemas.infrastructure import (
    AvailabilityBulkBody,
    BuildingCreate,
    BuildingOut,
    BuildingUpdate,
    ClassroomAvailOut,
    ClassroomCreate,
    ClassroomOut,
    ClassroomUpdate,
    ResourceAssignBody,
    ResourceCreate,
    ResourceOut,
    ResourceUpdate,
    RoomResourceOut,
)
from app.application.exceptions import ResourceNotFoundError
from app.application.commands.infrastructure_commands import (
    AssignResourceToClassroom,
    CreateBuilding,
    CreateClassroom,
    CreateResource,
    DeleteBuilding,
    DeleteClassroom,
    DeleteResource,
    SetClassroomAvailability,
    UpdateBuilding,
    UpdateClassroom,
    UpdateResource,
)
from app.application.queries.infrastructure_queries import (
    GetBuilding,
    GetClassroom,
    GetClassroomAvailability,
    GetResource,
    ListBuildings,
    ListClassroomResources,
    ListClassrooms,
    ListResources,
)
from app.domain.interfaces.unit_of_work import UnitOfWork

router = APIRouter(tags=["infrastructure"], dependencies=[Depends(get_current_user)])


# ── Buildings ───────────────────────────────────────────────────────────────


@router.post("/buildings", response_model=ApiResponse[BuildingOut], status_code=201)
async def create_building(
    body: BuildingCreate, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[BuildingOut]:
    entity = CreateBuilding(uow).execute(body)
    return ApiResponse(data=BuildingOut.model_validate(entity.__dict__), message="Building created")


@router.get("/campuses/{campus_id}/buildings", response_model=ApiResponse[list[BuildingOut]])
async def list_buildings(
    campus_id: UUID, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[BuildingOut]]:
    entities = ListBuildings(uow).execute(campus_id)
    return ApiResponse(data=[BuildingOut.model_validate(e.__dict__) for e in entities])


@router.get("/buildings/{building_id}", response_model=ApiResponse[BuildingOut])
async def get_building(
    building_id: UUID, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[BuildingOut]:
    entity = GetBuilding(uow).execute(building_id)
    return ApiResponse(data=BuildingOut.model_validate(entity.__dict__))


@router.put("/buildings/{building_id}", response_model=ApiResponse[BuildingOut])
async def update_building(
    building_id: UUID, body: BuildingUpdate, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[BuildingOut]:
    entity = UpdateBuilding(uow).execute(building_id, body)
    return ApiResponse(data=BuildingOut.model_validate(entity.__dict__), message="Building updated")


@router.delete("/buildings/{building_id}", response_model=ApiResponse[dict])
async def delete_building(
    building_id: UUID, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[dict]:
    DeleteBuilding(uow).execute(building_id)
    return ApiResponse(message="Building deleted", data={"deleted": True})


# ── Classrooms ──────────────────────────────────────────────────────────────


@router.post("/classrooms", response_model=ApiResponse[ClassroomOut], status_code=201)
async def create_classroom(
    body: ClassroomCreate, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ClassroomOut]:
    entity = CreateClassroom(uow).execute(body)
    return ApiResponse(data=ClassroomOut.model_validate(entity.__dict__), message="Classroom created")


@router.get(
    "/institutions/{institution_id}/classrooms",
    response_model=ApiResponse[list[ClassroomOut]],
)
async def list_classrooms(
    institution_id: UUID, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[ClassroomOut]]:
    entities = ListClassrooms(uow).execute(institution_id)
    return ApiResponse(data=[ClassroomOut.model_validate(e.__dict__) for e in entities])


@router.get("/classrooms/{classroom_id}", response_model=ApiResponse[ClassroomOut])
async def get_classroom(
    classroom_id: UUID, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ClassroomOut]:
    entity = GetClassroom(uow).execute(classroom_id)
    return ApiResponse(data=ClassroomOut.model_validate(entity.__dict__))


@router.put("/classrooms/{classroom_id}", response_model=ApiResponse[ClassroomOut])
async def update_classroom(
    classroom_id: UUID, body: ClassroomUpdate, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ClassroomOut]:
    entity = UpdateClassroom(uow).execute(classroom_id, body)
    return ApiResponse(data=ClassroomOut.model_validate(entity.__dict__), message="Classroom updated")


@router.delete("/classrooms/{classroom_id}", response_model=ApiResponse[dict])
async def delete_classroom(
    classroom_id: UUID, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[dict]:
    DeleteClassroom(uow).execute(classroom_id)
    return ApiResponse(message="Classroom deleted", data={"deleted": True})


# ── Classroom availability ──────────────────────────────────────────────────


@router.put(
    "/classrooms/{classroom_id}/availability",
    response_model=ApiResponse[dict],
)
async def set_classroom_availability(
    classroom_id: UUID,
    body: AvailabilityBulkBody,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[dict]:
    slots = [s.model_dump() for s in body.slots]
    count = SetClassroomAvailability(uow).execute(classroom_id, body.period_id, slots)
    return ApiResponse(data={"saved": count}, message="Availability updated")


@router.get(
    "/classrooms/{classroom_id}/availability",
    response_model=ApiResponse[list[ClassroomAvailOut]],
)
async def get_classroom_availability(
    classroom_id: UUID,
    period_id: UUID | None = None,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[ClassroomAvailOut]]:
    entities = GetClassroomAvailability(uow).execute(classroom_id, period_id)
    return ApiResponse(data=[ClassroomAvailOut.model_validate(e.__dict__) for e in entities])


# ── Resources ──────────────────────────────────────────────────────────────


@router.post("/resources", response_model=ApiResponse[ResourceOut], status_code=201)
async def create_resource(
    body: ResourceCreate, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ResourceOut]:
    entity = CreateResource(uow).execute(body)
    return ApiResponse(data=ResourceOut.model_validate(entity.__dict__), message="Resource created")


@router.get(
    "/institutions/{institution_id}/resources",
    response_model=ApiResponse[list[ResourceOut]],
)
async def list_resources(
    institution_id: UUID, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[ResourceOut]]:
    entities = ListResources(uow).execute(institution_id)
    return ApiResponse(data=[ResourceOut.model_validate(e.__dict__) for e in entities])


@router.get("/resources/{resource_id}", response_model=ApiResponse[ResourceOut])
async def get_resource(
    resource_id: UUID, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ResourceOut]:
    entity = GetResource(uow).execute(resource_id)
    return ApiResponse(data=ResourceOut.model_validate(entity.__dict__))


@router.put("/resources/{resource_id}", response_model=ApiResponse[ResourceOut])
async def update_resource(
    resource_id: UUID, body: ResourceUpdate, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ResourceOut]:
    entity = UpdateResource(uow).execute(resource_id, body)
    return ApiResponse(data=ResourceOut.model_validate(entity.__dict__), message="Resource updated")


@router.delete("/resources/{resource_id}", response_model=ApiResponse[dict])
async def delete_resource(
    resource_id: UUID, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[dict]:
    DeleteResource(uow).execute(resource_id)
    return ApiResponse(message="Resource deleted", data={"deleted": True})


# ── Classroom resource assignment ─────────────────────────────────────────


@router.post(
    "/classrooms/{classroom_id}/resources",
    response_model=ApiResponse[RoomResourceOut],
    status_code=201,
)
async def assign_resource_to_classroom(
    classroom_id: UUID,
    body: ResourceAssignBody,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[RoomResourceOut]:
    entity = AssignResourceToClassroom(uow).execute(
        classroom_id, body.resource_id, body.quantity,
    )
    return ApiResponse(
        data=RoomResourceOut.model_validate(entity.__dict__),
        message="Resource assigned",
    )


@router.get(
    "/classrooms/{classroom_id}/resources",
    response_model=ApiResponse[list[ResourceOut]],
)
async def list_classroom_resources(
    classroom_id: UUID, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[ResourceOut]]:
    entities = ListClassroomResources(uow).execute(classroom_id)
    return ApiResponse(data=[ResourceOut.model_validate(e.__dict__) for e in entities])


@router.delete(
    "/classrooms/{classroom_id}/resources/{resource_id}",
    response_model=ApiResponse[dict],
)
async def unassign_resource_from_classroom(
    classroom_id: UUID,
    resource_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[dict]:
    from app.infrastructure.persistence.models.infrastructure_models import (
        RoomResourceModel,
    )

    with uow:
        row = (
            uow._session.query(RoomResourceModel)
            .filter(
                RoomResourceModel.classroom_id == classroom_id,
                RoomResourceModel.resource_id == resource_id,
            )
            .first()
        )
        if row is None:
            raise ResourceNotFoundError("RoomResource", f"{classroom_id}/{resource_id}")
        uow._session.delete(row)
        uow.commit()
    return ApiResponse(message="Resource unassigned", data={"deleted": True})
