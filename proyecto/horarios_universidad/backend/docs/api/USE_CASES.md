# Use Cases

Each use case is a single-responsibility class with an `execute()` method.

## Institution Domain

| Use Case                 | Type    | File                                    |
|--------------------------|---------|-----------------------------------------|
| `CreateInstitution`      | Command | `commands/institution_commands.py`      |
| `UpdateInstitution`      | Command | `commands/institution_commands.py`      |
| `DeleteInstitution`      | Command | `commands/institution_commands.py`      |
| `CreateCampus`           | Command | `commands/institution_commands.py`      |
| `UpdateCampus`           | Command | `commands/institution_commands.py`      |
| `CreateAcademicPeriod`   | Command | `commands/institution_commands.py`      |
| `UpdateAcademicPeriod`   | Command | `commands/institution_commands.py`      |
| `CloneAcademicPeriod`    | Command | `commands/institution_commands.py`      |
| `GetInstitution`         | Query   | `queries/institution_queries.py`        |
| `ListInstitutions`       | Query   | `queries/institution_queries.py`        |
| `GetCampus`              | Query   | `queries/institution_queries.py`        |
| `ListCampuses`           | Query   | `queries/institution_queries.py`        |
| `GetAcademicPeriod`      | Query   | `queries/institution_queries.py`        |
| `ListAcademicPeriods`    | Query   | `queries/institution_queries.py`        |
| `GetActiveAcademicPeriod`| Query   | `queries/institution_queries.py`        |

## Academic Domain

| Use Case                 | Type    | File                                    |
|--------------------------|---------|-----------------------------------------|
| `CreateArea`             | Command | `commands/academic_commands.py`         |
| `UpdateArea`             | Command | `commands/academic_commands.py`         |
| `DeleteArea`             | Command | `commands/academic_commands.py`         |
| `CreateSubject`          | Command | `commands/academic_commands.py`         |
| `UpdateSubject`          | Command | `commands/academic_commands.py`         |
| `DeleteSubject`          | Command | `commands/academic_commands.py`         |

## Personnel Domain

| Use Case                 | Type    | File                                    |
|--------------------------|---------|-----------------------------------------|
| `CreateTeacher`          | Command | `commands/personnel_commands.py`        |
| `UpdateTeacher`          | Command | `commands/personnel_commands.py`        |
| `DeleteTeacher`          | Command | `commands/personnel_commands.py`        |
| `CreateTeacherContract`  | Command | `commands/personnel_commands.py`        |
| `UpdateTeacherContract`  | Command | `commands/personnel_commands.py`        |
| `AssignTeacherSubject`   | Command | `commands/personnel_commands.py`        |
| `RemoveTeacherSubject`   | Command | `commands/personnel_commands.py`        |
| `SetTeacherAvailability` | Command | `commands/personnel_commands.py`        |
| `SetTeacherPreference`   | Command | `commands/personnel_commands.py`        |
| `GetTeacher`             | Query   | `queries/personnel_queries.py`          |
| `ListTeachers`           | Query   | `queries/personnel_queries.py`          |
| `GetTeacherDetail`       | Query   | `queries/personnel_queries.py`          |
| `GetTeacherAvailability` | Query   | `queries/personnel_queries.py`          |
| `GetTeacherSpecialties`  | Query   | `queries/personnel_queries.py`          |
| `GetTeacherPreferences`  | Query   | `queries/personnel_queries.py`          |

## Infrastructure Domain

| Use Case                     | Type    | File                                      |
|------------------------------|---------|-------------------------------------------|
| `CreateBuilding`             | Command | `commands/infrastructure_commands.py`     |
| `UpdateBuilding`             | Command | `commands/infrastructure_commands.py`     |
| `DeleteBuilding`             | Command | `commands/infrastructure_commands.py`     |
| `CreateClassroom`            | Command | `commands/infrastructure_commands.py`     |
| `UpdateClassroom`            | Command | `commands/infrastructure_commands.py`     |
| `DeleteClassroom`            | Command | `commands/infrastructure_commands.py`     |
| `SetClassroomAvailability`   | Command | `commands/infrastructure_commands.py`     |
| `CreateResource`             | Command | `commands/infrastructure_commands.py`     |
| `UpdateResource`             | Command | `commands/infrastructure_commands.py`     |
| `DeleteResource`             | Command | `commands/infrastructure_commands.py`     |
| `AssignResourceToClassroom`  | Command | `commands/infrastructure_commands.py`     |
| `GetBuilding`                | Query   | `queries/infrastructure_queries.py`       |
| `ListBuildings`              | Query   | `queries/infrastructure_queries.py`       |
| `GetClassroom`               | Query   | `queries/infrastructure_queries.py`       |
| `ListClassrooms`             | Query   | `queries/infrastructure_queries.py`       |
| `GetClassroomAvailability`   | Query   | `queries/infrastructure_queries.py`       |
| `GetResource`                | Query   | `queries/infrastructure_queries.py`       |
| `ListResources`              | Query   | `queries/infrastructure_queries.py`       |
| `ListClassroomResources`     | Query   | `queries/infrastructure_queries.py`       |

## Offering Domain

| Use Case                     | Type    | File                                      |
|------------------------------|---------|-------------------------------------------|
| `CreateOffering`             | Command | `commands/offering_commands.py`           |
| `UpdateOffering`             | Command | `commands/offering_commands.py`           |
| `DeleteOffering`             | Command | `commands/offering_commands.py`           |
| `AddOfferingLine`            | Command | `commands/offering_commands.py`           |
| `UpdateOfferingLine`         | Command | `commands/offering_commands.py`           |
| `RemoveOfferingLine`         | Command | `commands/offering_commands.py`           |
| `CreateScheduleType`         | Command | `commands/offering_commands.py`           |
| `UpdateScheduleType`         | Command | `commands/offering_commands.py`           |
| `DeleteScheduleType`         | Command | `commands/offering_commands.py`           |
| `CreateGroup`                | Command | `commands/offering_commands.py`           |
| `DeleteGroup`                | Command | `commands/offering_commands.py`           |
| `GenerateGroupsFromOffering` | Command | `commands/offering_commands.py`           |

## Schedule Domain

| Use Case                 | Type    | File                                    |
|--------------------------|---------|-----------------------------------------|
| `GenerateSchedule`       | Command | `commands/schedule_commands.py`         |
| `ValidateScheduleData`   | Command | `commands/schedule_commands.py`         |
| `PublishSchedule`        | Command | `commands/schedule_commands.py`         |
| `BlockSchedule`          | Command | `commands/schedule_commands.py`         |
| `GetScheduleRun`         | Query   | `queries/schedule_queries.py`           |
| `ListScheduleRuns`       | Query   | `queries/schedule_queries.py`           |
| `GetScheduleAssignments` | Query   | `queries/schedule_queries.py`           |
| `GetScheduleRunDetail`   | Query   | `queries/schedule_queries.py`           |
| `GetValidationReport`    | Query   | `queries/schedule_queries.py`           |

## Dashboard

| Use Case                 | Type    | File                                    |
|--------------------------|---------|-----------------------------------------|
| `GetDashboard`           | Query   | `queries/dashboard_queries.py`          |
