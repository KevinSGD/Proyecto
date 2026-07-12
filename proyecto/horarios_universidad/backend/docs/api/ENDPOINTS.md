# API Endpoints

Base URL: `/api/v1`

## Health

| Method | Path      | Description        |
|--------|-----------|--------------------|
| GET    | `/health` | Health check (no prefix) |

## Institutions

| Method | Path                                              | Status | Description                |
|--------|---------------------------------------------------|--------|----------------------------|
| POST   | `/institutions`                                   | 201    | Create institution         |
| GET    | `/institutions`                                   | 200    | List all institutions      |
| GET    | `/institutions/{id}`                              | 200    | Get institution by ID      |
| PUT    | `/institutions/{id}`                              | 200    | Update institution         |
| DELETE | `/institutions/{id}`                              | 204    | Delete institution         |

## Campuses

| Method | Path                                              | Status | Description                |
|--------|---------------------------------------------------|--------|----------------------------|
| POST   | `/institutions/{id}/campuses`                     | 201    | Create campus              |
| GET    | `/institutions/{id}/campuses`                     | 200    | List campuses              |
| GET    | `/campuses/{id}`                                  | 200    | Get campus by ID           |
| PUT    | `/campuses/{id}`                                  | 200    | Update campus              |

## Academic Periods

| Method | Path                                              | Status | Description                |
|--------|---------------------------------------------------|--------|----------------------------|
| POST   | `/institutions/{id}/periods`                      | 201    | Create period              |
| GET    | `/institutions/{id}/periods`                      | 200    | List periods               |
| GET    | `/institutions/{id}/periods/active`               | 200    | Get active period          |
| GET    | `/periods/{id}`                                   | 200    | Get period by ID           |
| PUT    | `/periods/{id}`                                   | 200    | Update period              |
| POST   | `/periods/{id}/clone`                             | 201    | Clone period               |

## Academic (Areas, Subjects)

| Method | Path                                              | Status | Description                |
|--------|---------------------------------------------------|--------|----------------------------|
| POST   | `/institutions/{id}/areas`                        | 201    | Create area + coordinator  |
| GET    | `/institutions/{id}/areas`                        | 200    | List areas                 |
| GET    | `/areas/{id}`                                     | 200    | Get area                   |
| PUT    | `/areas/{id}`                                     | 200    | Update area                |
| DELETE | `/areas/{id}`                                     | 200    | Delete area                |
| POST   | `/institutions/{id}/subjects`                     | 201    | Create subject             |
| GET    | `/institutions/{id}/subjects`                     | 200    | List subjects              |
| GET    | `/subjects/{id}`                                  | 200    | Get subject                |
| PUT    | `/subjects/{id}`                                  | 200    | Update subject             |
| DELETE | `/subjects/{id}`                                  | 200    | Delete subject             |

## Teachers (Personnel)

| Method | Path                                              | Status | Description                |
|--------|---------------------------------------------------|--------|----------------------------|
| POST   | `/teachers`                                       | 201    | Create teacher             |
| GET    | `/institutions/{id}/teachers`                     | 200    | List teachers              |
| GET    | `/teachers/{id}`                                  | 200    | Get teacher                |
| GET    | `/teachers/{id}/detail`                           | 200    | Get teacher with details   |
| PUT    | `/teachers/{id}`                                  | 200    | Update teacher             |
| DELETE | `/teachers/{id}`                                  | 200    | Delete teacher             |
| POST   | `/teachers/{id}/contracts`                        | 201    | Create contract            |
| PUT    | `/contracts/{id}`                                 | 200    | Update contract            |
| POST   | `/teachers/{id}/specialties`                      | 201    | Assign specialty           |
| DELETE | `/specialties/{id}`                               | 200    | Remove specialty           |
| GET    | `/teachers/{id}/specialties`                      | 200    | List specialties           |
| PUT    | `/teachers/{id}/availability`                     | 200    | Set availability           |
| GET    | `/teachers/{id}/availability`                     | 200    | Get availability           |
| POST   | `/teachers/{id}/preferences`                      | 201    | Set preference             |
| GET    | `/teachers/{id}/preferences`                      | 200    | Get preferences            |

## Infrastructure

| Method | Path                                              | Status | Description                |
|--------|---------------------------------------------------|--------|----------------------------|
| POST   | `/buildings`                                      | 201    | Create building            |
| GET    | `/campuses/{id}/buildings`                        | 200    | List buildings             |
| GET    | `/buildings/{id}`                                 | 200    | Get building               |
| PUT    | `/buildings/{id}`                                 | 200    | Update building            |
| DELETE | `/buildings/{id}`                                 | 200    | Delete building            |
| POST   | `/classrooms`                                     | 201    | Create classroom           |
| GET    | `/institutions/{id}/classrooms`                   | 200    | List classrooms            |
| GET    | `/classrooms/{id}`                                | 200    | Get classroom              |
| PUT    | `/classrooms/{id}`                                | 200    | Update classroom           |
| DELETE | `/classrooms/{id}`                                | 200    | Delete classroom           |
| PUT    | `/classrooms/{id}/availability`                   | 200    | Set classroom availability |
| GET    | `/classrooms/{id}/availability`                   | 200    | Get classroom availability |
| POST   | `/resources`                                      | 201    | Create resource            |
| GET    | `/institutions/{id}/resources`                    | 200    | List resources             |
| GET    | `/resources/{id}`                                 | 200    | Get resource               |
| PUT    | `/resources/{id}`                                 | 200    | Update resource            |
| DELETE | `/resources/{id}`                                 | 200    | Delete resource            |
| POST   | `/classrooms/{id}/resources`                      | 201    | Assign resource            |
| GET    | `/classrooms/{id}/resources`                      | 200    | List classroom resources   |

## Offerings

| Method | Path                                              | Status | Description                |
|--------|---------------------------------------------------|--------|----------------------------|
| POST   | `/offerings`                                      | 201    | Create offering            |
| GET    | `/institutions/{id}/periods/{pid}/offerings`      | 200    | List offerings             |
| GET    | `/offerings/{id}`                                 | 200    | Get offering               |
| PUT    | `/offerings/{id}`                                 | 200    | Update offering            |
| DELETE | `/offerings/{id}`                                 | 200    | Delete offering            |
| POST   | `/offerings/{id}/lines`                           | 201    | Add offering line          |
| PUT    | `/offering-lines/{id}`                            | 200    | Update offering line       |
| DELETE | `/offering-lines/{id}`                            | 200    | Remove offering line       |
| POST   | `/schedule-types`                                 | 201    | Create schedule type       |
| GET    | `/institutions/{id}/schedule-types`               | 200    | List schedule types        |
| PUT    | `/schedule-types/{id}`                            | 200    | Update schedule type       |
| DELETE | `/schedule-types/{id}`                            | 200    | Delete schedule type       |
| POST   | `/groups`                                         | 201    | Create group               |
| DELETE | `/groups/{id}`                                    | 200    | Delete group               |
| POST   | `/offerings/{id}/generate-groups`                 | 201    | Auto-generate groups       |

## Schedule

| Method | Path                                                          | Status | Description              |
|--------|---------------------------------------------------------------|--------|--------------------------|
| POST   | `/schedule/generate`                                          | 201    | Generate schedule        |
| POST   | `/schedule/validate`                                          | 200    | Validate data            |
| POST   | `/schedule/publish`                                           | 200    | Publish schedule run     |
| POST   | `/schedule/block`                                             | 200    | Block schedule run       |
| GET    | `/institutions/{id}/periods/{pid}/schedule-runs`              | 200    | List schedule runs       |
| GET    | `/schedule-runs/{id}`                                         | 200    | Get schedule run         |
| GET    | `/schedule-runs/{id}/assignments`                             | 200    | Get assignments          |
| GET    | `/schedule-runs/{id}/detail`                                  | 200    | Get run with assignments |
| GET    | `/validation-reports/{id}`                                    | 200    | Get validation report    |

## Dashboard

| Method | Path                                                          | Status | Description              |
|--------|---------------------------------------------------------------|--------|--------------------------|
| GET    | `/institutions/{id}/dashboard`                                | 200    | Dashboard (auto period)  |
| GET    | `/institutions/{id}/periods/{pid}/dashboard`                  | 200    | Dashboard (specific)     |
