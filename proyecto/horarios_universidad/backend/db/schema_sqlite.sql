CREATE TABLE academic_areas (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	description VARCHAR(1000) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_academic_areas_institution_code UNIQUE (institution_id, code)
);

CREATE INDEX ix_academic_areas_institution_id ON academic_areas (institution_id);

CREATE TABLE institutions (
	id CHAR(32) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	abbreviation VARCHAR(50) NOT NULL, 
	address VARCHAR(500) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(50) NOT NULL, 
	website VARCHAR(255) NOT NULL, 
	logo_url VARCHAR(500) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	metadata JSON NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_institutions_abbreviation UNIQUE (abbreviation)
);

CREATE TABLE academic_periods (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	year INTEGER NOT NULL, 
	period_number INTEGER NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	start_date DATE, 
	end_date DATE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_academic_periods_institution_year_period UNIQUE (institution_id, year, period_number), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id)
);

CREATE INDEX ix_academic_periods_institution_id ON academic_periods (institution_id);

CREATE TABLE campuses (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	address VARCHAR(500) NOT NULL, 
	city VARCHAR(255) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_campuses_institution_code UNIQUE (institution_id, code), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id)
);

CREATE INDEX ix_campuses_institution_id ON campuses (institution_id);

CREATE TABLE import_templates (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32), 
	name VARCHAR(255) NOT NULL, 
	entity_type VARCHAR(100) NOT NULL, 
	version VARCHAR(50) NOT NULL, 
	column_mappings JSON NOT NULL, 
	transformation_rules JSON NOT NULL, 
	validation_rules JSON NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_import_templates_institution_name_type UNIQUE (institution_id, name, entity_type), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id)
);

CREATE INDEX ix_import_templates_institution_id ON import_templates (institution_id);

CREATE TABLE instructors (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32) NOT NULL, 
	area_id CHAR(32), 
	employee_code VARCHAR(50) NOT NULL, 
	first_name VARCHAR(255) NOT NULL, 
	last_name VARCHAR(255) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(50) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_instructors_institution_employee_code UNIQUE (institution_id, employee_code), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id), 
	FOREIGN KEY(area_id) REFERENCES academic_areas (id)
);

CREATE INDEX ix_instructors_area_id ON instructors (area_id);

CREATE INDEX ix_instructors_institution_id ON instructors (institution_id);

CREATE TABLE resources (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	description VARCHAR(1000) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_resources_institution_code UNIQUE (institution_id, code), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id)
);

CREATE INDEX ix_resources_institution_id ON resources (institution_id);

CREATE TABLE roles (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32), 
	name VARCHAR(100) NOT NULL, 
	description VARCHAR(500) NOT NULL, 
	is_system BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_roles_institution_name UNIQUE (institution_id, name), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id)
);

CREATE INDEX ix_roles_institution_id ON roles (institution_id);

CREATE TABLE schedule_types (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	schedule_type VARCHAR(100) NOT NULL, 
	active_days JSON NOT NULL, 
	start_period INTEGER NOT NULL, 
	end_period INTEGER NOT NULL, 
	slot_duration_minutes INTEGER NOT NULL, 
	start_hour INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_schedule_types_institution_name UNIQUE (institution_id, name), 
	CONSTRAINT ck_schedule_types_start_period CHECK (start_period >= 0), 
	CONSTRAINT ck_schedule_types_end_period CHECK (end_period >= start_period), 
	CONSTRAINT ck_schedule_types_slot_duration CHECK (slot_duration_minutes > 0), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id)
);

CREATE INDEX ix_schedule_types_institution_id ON schedule_types (institution_id);

CREATE TABLE subjects (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32) NOT NULL, 
	area_id CHAR(32), 
	code VARCHAR(50) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	credit_hours INTEGER NOT NULL, 
	weekly_hours INTEGER NOT NULL, 
	modality_default VARCHAR(50) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_subjects_institution_code UNIQUE (institution_id, code), 
	FOREIGN KEY(area_id) REFERENCES academic_areas (id)
);

CREATE INDEX ix_subjects_area_id ON subjects (area_id);

CREATE INDEX ix_subjects_institution_id ON subjects (institution_id);

CREATE TABLE system_parameters (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32), 
	"key" VARCHAR(255) NOT NULL, 
	value VARCHAR(2000) NOT NULL, 
	value_type VARCHAR(50) NOT NULL, 
	description VARCHAR(1000) NOT NULL, 
	is_editable BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_system_parameters_institution_key UNIQUE (institution_id, "key"), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id)
);

CREATE INDEX ix_system_parameters_institution_id ON system_parameters (institution_id);

CREATE TABLE buildings (
	id CHAR(32) NOT NULL, 
	campus_id CHAR(32) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	floors INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_buildings_campus_code UNIQUE (campus_id, code), 
	CONSTRAINT ck_buildings_floors CHECK (floors >= 1), 
	FOREIGN KEY(campus_id) REFERENCES campuses (id)
);

CREATE INDEX ix_buildings_campus_id ON buildings (campus_id);

CREATE TABLE instructor_availabilities (
	id CHAR(32) NOT NULL, 
	instructor_id CHAR(32) NOT NULL, 
	period_id CHAR(32), 
	day_of_week INTEGER NOT NULL, 
	period INTEGER NOT NULL, 
	is_available BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_instructor_availabilities_slot UNIQUE (instructor_id, period_id, day_of_week, period), 
	CONSTRAINT ck_instructor_availabilities_day CHECK (day_of_week >= 0 AND day_of_week <= 6), 
	CONSTRAINT ck_instructor_availabilities_period CHECK (period >= 1), 
	FOREIGN KEY(instructor_id) REFERENCES instructors (id), 
	FOREIGN KEY(period_id) REFERENCES academic_periods (id)
);

CREATE INDEX ix_instructor_availabilities_instructor_id ON instructor_availabilities (instructor_id);

CREATE INDEX ix_instructor_availabilities_period_id ON instructor_availabilities (period_id);

CREATE TABLE instructor_contracts (
	id CHAR(32) NOT NULL, 
	instructor_id CHAR(32) NOT NULL, 
	contract_type VARCHAR(100) NOT NULL, 
	start_date DATE, 
	end_date DATE, 
	max_daily_periods INTEGER NOT NULL, 
	max_weekly_periods INTEGER NOT NULL, 
	min_weekly_periods INTEGER NOT NULL, 
	max_days INTEGER, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(instructor_id) REFERENCES instructors (id)
);

CREATE INDEX ix_instructor_contracts_instructor_id ON instructor_contracts (instructor_id);

CREATE TABLE instructor_qualifications (
	id CHAR(32) NOT NULL, 
	instructor_id CHAR(32) NOT NULL, 
	qualification_type VARCHAR(100) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	institution_name VARCHAR(255) NOT NULL, 
	year_obtained INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(instructor_id) REFERENCES instructors (id)
);

CREATE INDEX ix_instructor_qualifications_instructor_id ON instructor_qualifications (instructor_id);

CREATE TABLE instructor_specialties (
	id CHAR(32) NOT NULL, 
	instructor_id CHAR(32) NOT NULL, 
	subject_id CHAR(32) NOT NULL, 
	proficiency_level INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_instructor_specialties_instructor_subject UNIQUE (instructor_id, subject_id), 
	CONSTRAINT ck_instructor_specialties_proficiency CHECK (proficiency_level >= 1 AND proficiency_level <= 10), 
	FOREIGN KEY(instructor_id) REFERENCES instructors (id), 
	FOREIGN KEY(subject_id) REFERENCES subjects (id)
);

CREATE INDEX ix_instructor_specialties_subject_id ON instructor_specialties (subject_id);

CREATE INDEX ix_instructor_specialties_instructor_id ON instructor_specialties (instructor_id);

CREATE TABLE permissions (
	id CHAR(32) NOT NULL, 
	role_id CHAR(32) NOT NULL, 
	resource VARCHAR(255) NOT NULL, 
	action VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_permissions_role_resource_action UNIQUE (role_id, resource, action), 
	FOREIGN KEY(role_id) REFERENCES roles (id)
);

CREATE INDEX ix_permissions_role_id ON permissions (role_id);

CREATE TABLE subject_resource_requirements (
	id CHAR(32) NOT NULL, 
	subject_id CHAR(32) NOT NULL, 
	resource_id CHAR(32) NOT NULL, 
	is_mandatory BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_subject_resource_requirements_pair UNIQUE (subject_id, resource_id), 
	FOREIGN KEY(subject_id) REFERENCES subjects (id), 
	FOREIGN KEY(resource_id) REFERENCES resources (id)
);

CREATE INDEX ix_subject_resource_requirements_subject_id ON subject_resource_requirements (subject_id);

CREATE INDEX ix_subject_resource_requirements_resource_id ON subject_resource_requirements (resource_id);

CREATE TABLE users (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32), 
	role_id CHAR(32), 
	email VARCHAR(255) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	phone VARCHAR(50) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	hashed_password VARCHAR(255) NOT NULL, 
	last_login DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id), 
	FOREIGN KEY(role_id) REFERENCES roles (id), 
	UNIQUE (email)
);

CREATE INDEX ix_users_role_id ON users (role_id);

CREATE INDEX ix_users_institution_id ON users (institution_id);

CREATE TABLE academic_offerings (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32) NOT NULL, 
	period_id CHAR(32) NOT NULL, 
	area_id CHAR(32) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	observations VARCHAR(2000) NOT NULL, 
	created_by CHAR(32), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_academic_offerings_institution_period_area UNIQUE (institution_id, period_id, area_id), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id), 
	FOREIGN KEY(period_id) REFERENCES academic_periods (id), 
	FOREIGN KEY(area_id) REFERENCES academic_areas (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE INDEX ix_academic_offerings_institution_id ON academic_offerings (institution_id);

CREATE INDEX ix_academic_offerings_area_id ON academic_offerings (area_id);

CREATE INDEX ix_academic_offerings_period_id ON academic_offerings (period_id);

CREATE TABLE audit_logs (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32), 
	user_id CHAR(32), 
	entity_type VARCHAR(100) NOT NULL, 
	entity_id CHAR(32), 
	action VARCHAR(50) NOT NULL, 
	old_values JSON NOT NULL, 
	new_values JSON NOT NULL, 
	ip_address VARCHAR(45), 
	timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_audit_logs_institution_id ON audit_logs (institution_id);

CREATE INDEX ix_audit_logs_entity_id ON audit_logs (entity_id);

CREATE INDEX ix_audit_logs_timestamp ON audit_logs (timestamp);

CREATE INDEX ix_audit_logs_entity_type ON audit_logs (entity_type);

CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);

CREATE INDEX ix_audit_logs_action ON audit_logs (action);

CREATE TABLE classrooms (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32) NOT NULL, 
	building_id CHAR(32), 
	name VARCHAR(255) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	capacity INTEGER NOT NULL, 
	floor INTEGER, 
	is_virtual BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_classrooms_institution_code UNIQUE (institution_id, code), 
	CONSTRAINT ck_classrooms_capacity CHECK (capacity >= 0), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id), 
	FOREIGN KEY(building_id) REFERENCES buildings (id)
);

CREATE INDEX ix_classrooms_institution_id ON classrooms (institution_id);

CREATE INDEX ix_classrooms_building_id ON classrooms (building_id);

CREATE TABLE import_sessions (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32) NOT NULL, 
	user_id CHAR(32), 
	filename VARCHAR(500) NOT NULL, 
	entity_type VARCHAR(100) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	total_rows INTEGER NOT NULL, 
	processed_rows INTEGER NOT NULL, 
	error_rows INTEGER NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	completed_at DATETIME, 
	rollback_data JSON NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_import_sessions_total_rows CHECK (total_rows >= 0), 
	CONSTRAINT ck_import_sessions_processed_rows CHECK (processed_rows >= 0), 
	CONSTRAINT ck_import_sessions_error_rows CHECK (error_rows >= 0), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_import_sessions_entity_type ON import_sessions (entity_type);

CREATE INDEX ix_import_sessions_user_id ON import_sessions (user_id);

CREATE INDEX ix_import_sessions_institution_id ON import_sessions (institution_id);

CREATE TABLE notifications (
	id CHAR(32) NOT NULL, 
	user_id CHAR(32) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	message VARCHAR(2000) NOT NULL, 
	notification_type VARCHAR(50) NOT NULL, 
	is_read BOOLEAN NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	metadata JSON NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_notifications_user_id ON notifications (user_id);

CREATE TABLE optimization_configs (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32) NOT NULL, 
	period_id CHAR(32), 
	name VARCHAR(255) NOT NULL, 
	config_data JSON NOT NULL, 
	is_default BOOLEAN NOT NULL, 
	created_at DATETIME, 
	created_by CHAR(32), 
	PRIMARY KEY (id), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id), 
	FOREIGN KEY(period_id) REFERENCES academic_periods (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE INDEX ix_optimization_configs_period_id ON optimization_configs (period_id);

CREATE INDEX ix_optimization_configs_institution_id ON optimization_configs (institution_id);

CREATE TABLE user_areas (
	id CHAR(32) NOT NULL, 
	user_id CHAR(32) NOT NULL, 
	area_id CHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_areas_user_area UNIQUE (user_id, area_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(area_id) REFERENCES academic_areas (id)
);

CREATE INDEX ix_user_areas_area_id ON user_areas (area_id);

CREATE INDEX ix_user_areas_user_id ON user_areas (user_id);

CREATE TABLE validation_reports (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32) NOT NULL, 
	period_id CHAR(32), 
	report_type VARCHAR(100) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	errors JSON NOT NULL, 
	warnings JSON NOT NULL, 
	summary JSON NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by CHAR(32), 
	PRIMARY KEY (id), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id), 
	FOREIGN KEY(period_id) REFERENCES academic_periods (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE INDEX ix_validation_reports_period_id ON validation_reports (period_id);

CREATE INDEX ix_validation_reports_institution_id ON validation_reports (institution_id);

CREATE TABLE classroom_availabilities (
	id CHAR(32) NOT NULL, 
	classroom_id CHAR(32) NOT NULL, 
	period_id CHAR(32), 
	day_of_week INTEGER NOT NULL, 
	period INTEGER NOT NULL, 
	is_available BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_classroom_availabilities_slot UNIQUE (classroom_id, period_id, day_of_week, period), 
	CONSTRAINT ck_classroom_availabilities_day CHECK (day_of_week >= 0 AND day_of_week <= 6), 
	CONSTRAINT ck_classroom_availabilities_period CHECK (period >= 1), 
	FOREIGN KEY(classroom_id) REFERENCES classrooms (id), 
	FOREIGN KEY(period_id) REFERENCES academic_periods (id)
);

CREATE INDEX ix_classroom_availabilities_period_id ON classroom_availabilities (period_id);

CREATE INDEX ix_classroom_availabilities_classroom_id ON classroom_availabilities (classroom_id);

CREATE TABLE import_log_entries (
	id CHAR(32) NOT NULL, 
	import_session_id CHAR(32) NOT NULL, 
	row_number INTEGER NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	entity_id CHAR(32), 
	error_message VARCHAR(2000) NOT NULL, 
	raw_data JSON NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(import_session_id) REFERENCES import_sessions (id)
);

CREATE INDEX ix_import_log_entries_import_session_id ON import_log_entries (import_session_id);

CREATE TABLE offering_lines (
	id CHAR(32) NOT NULL, 
	offering_id CHAR(32) NOT NULL, 
	subject_id CHAR(32) NOT NULL, 
	num_groups INTEGER NOT NULL, 
	expected_enrollment_per_group INTEGER NOT NULL, 
	modality VARCHAR(50) NOT NULL, 
	schedule_type_id CHAR(32), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_offering_lines_offering_subject UNIQUE (offering_id, subject_id), 
	CONSTRAINT ck_offering_lines_num_groups CHECK (num_groups >= 0), 
	CONSTRAINT ck_offering_lines_enrollment CHECK (expected_enrollment_per_group >= 0), 
	FOREIGN KEY(offering_id) REFERENCES academic_offerings (id), 
	FOREIGN KEY(subject_id) REFERENCES subjects (id), 
	FOREIGN KEY(schedule_type_id) REFERENCES schedule_types (id)
);

CREATE INDEX ix_offering_lines_schedule_type_id ON offering_lines (schedule_type_id);

CREATE INDEX ix_offering_lines_offering_id ON offering_lines (offering_id);

CREATE INDEX ix_offering_lines_subject_id ON offering_lines (subject_id);

CREATE TABLE room_resources (
	id CHAR(32) NOT NULL, 
	classroom_id CHAR(32) NOT NULL, 
	resource_id CHAR(32) NOT NULL, 
	quantity INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_room_resources_pair UNIQUE (classroom_id, resource_id), 
	CONSTRAINT ck_room_resources_quantity CHECK (quantity >= 1), 
	FOREIGN KEY(classroom_id) REFERENCES classrooms (id), 
	FOREIGN KEY(resource_id) REFERENCES resources (id)
);

CREATE INDEX ix_room_resources_resource_id ON room_resources (resource_id);

CREATE INDEX ix_room_resources_classroom_id ON room_resources (classroom_id);

CREATE TABLE schedule_runs (
	id CHAR(32) NOT NULL, 
	institution_id CHAR(32) NOT NULL, 
	period_id CHAR(32) NOT NULL, 
	config_id CHAR(32), 
	name VARCHAR(200) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	solver_config JSON NOT NULL, 
	statistics JSON NOT NULL, 
	started_at DATETIME, 
	completed_at DATETIME, 
	objective_value FLOAT, 
	gap FLOAT, 
	created_by CHAR(32), 
	PRIMARY KEY (id), 
	FOREIGN KEY(institution_id) REFERENCES institutions (id), 
	FOREIGN KEY(period_id) REFERENCES academic_periods (id), 
	FOREIGN KEY(config_id) REFERENCES optimization_configs (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE INDEX ix_schedule_runs_period_id ON schedule_runs (period_id);

CREATE INDEX ix_schedule_runs_config_id ON schedule_runs (config_id);

CREATE INDEX ix_schedule_runs_institution_id ON schedule_runs (institution_id);

CREATE TABLE execution_logs (
	id CHAR(32) NOT NULL, 
	schedule_run_id CHAR(32) NOT NULL, 
	event_type VARCHAR(100) NOT NULL, 
	message VARCHAR(2000) NOT NULL, 
	timestamp DATETIME, 
	metadata JSON NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(schedule_run_id) REFERENCES schedule_runs (id)
);

CREATE INDEX ix_execution_logs_schedule_run_id ON execution_logs (schedule_run_id);

CREATE TABLE groups (
	id CHAR(32) NOT NULL, 
	offering_line_id CHAR(32) NOT NULL, 
	subject_id CHAR(32) NOT NULL, 
	group_number INTEGER NOT NULL, 
	expected_enrollment INTEGER NOT NULL, 
	modality VARCHAR(50) NOT NULL, 
	schedule_type_id CHAR(32) NOT NULL, 
	priority INTEGER NOT NULL, 
	assigned_instructor_id CHAR(32), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_groups_offering_line_number UNIQUE (offering_line_id, group_number), 
	CONSTRAINT ck_groups_group_number CHECK (group_number >= 0), 
	CONSTRAINT ck_groups_enrollment CHECK (expected_enrollment >= 0), 
	CONSTRAINT ck_groups_priority CHECK (priority >= 1 AND priority <= 5), 
	FOREIGN KEY(offering_line_id) REFERENCES offering_lines (id), 
	FOREIGN KEY(subject_id) REFERENCES subjects (id), 
	FOREIGN KEY(schedule_type_id) REFERENCES schedule_types (id), 
	FOREIGN KEY(assigned_instructor_id) REFERENCES instructors (id)
);

CREATE INDEX ix_groups_offering_line_id ON groups (offering_line_id);

CREATE INDEX ix_groups_schedule_type_id ON groups (schedule_type_id);

CREATE INDEX ix_groups_assigned_instructor_id ON groups (assigned_instructor_id);

CREATE INDEX ix_groups_subject_id ON groups (subject_id);

CREATE TABLE assignments (
	id CHAR(32) NOT NULL, 
	schedule_run_id CHAR(32) NOT NULL, 
	group_id CHAR(32) NOT NULL, 
	instructor_id CHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_assignments_run_group UNIQUE (schedule_run_id, group_id), 
	FOREIGN KEY(schedule_run_id) REFERENCES schedule_runs (id), 
	FOREIGN KEY(group_id) REFERENCES groups (id), 
	FOREIGN KEY(instructor_id) REFERENCES instructors (id)
);

CREATE INDEX ix_assignments_schedule_run_id ON assignments (schedule_run_id);

CREATE INDEX ix_assignments_instructor_id ON assignments (instructor_id);

CREATE INDEX ix_assignments_group_id ON assignments (group_id);

CREATE TABLE instructor_preferences (
	id CHAR(32) NOT NULL, 
	instructor_id CHAR(32) NOT NULL, 
	period_id CHAR(32), 
	group_id CHAR(32), 
	subject_id CHAR(32), 
	score INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_instructor_preferences_score CHECK (score >= 1 AND score <= 10), 
	FOREIGN KEY(instructor_id) REFERENCES instructors (id), 
	FOREIGN KEY(period_id) REFERENCES academic_periods (id), 
	FOREIGN KEY(group_id) REFERENCES groups (id), 
	FOREIGN KEY(subject_id) REFERENCES subjects (id)
);

CREATE INDEX ix_instructor_preferences_group_id ON instructor_preferences (group_id);

CREATE INDEX ix_instructor_preferences_subject_id ON instructor_preferences (subject_id);

CREATE INDEX ix_instructor_preferences_period_id ON instructor_preferences (period_id);

CREATE INDEX ix_instructor_preferences_instructor_id ON instructor_preferences (instructor_id);

CREATE TABLE session_blocks (
	id CHAR(32) NOT NULL, 
	assignment_id CHAR(32) NOT NULL, 
	block_index INTEGER NOT NULL, 
	day_of_week INTEGER NOT NULL, 
	start_period INTEGER NOT NULL, 
	duration INTEGER NOT NULL, 
	classroom_id CHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_session_blocks_day CHECK (day_of_week >= 0 AND day_of_week <= 6), 
	CONSTRAINT ck_session_blocks_start_period CHECK (start_period >= 1), 
	CONSTRAINT ck_session_blocks_duration CHECK (duration >= 1), 
	FOREIGN KEY(assignment_id) REFERENCES assignments (id), 
	FOREIGN KEY(classroom_id) REFERENCES classrooms (id)
);

CREATE INDEX ix_session_blocks_classroom_id ON session_blocks (classroom_id);

CREATE INDEX ix_session_blocks_assignment_id ON session_blocks (assignment_id);