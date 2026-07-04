"""Unit tests for domain entities."""

from __future__ import annotations

import uuid

from app.domain.entities.institution import Institution
from app.domain.entities.scheduling import Group
from app.domain.entities.personnel import Instructor


class TestInstitution:
    def test_default_id_is_uuid(self) -> None:
        inst = Institution()
        assert isinstance(inst.id, uuid.UUID)

    def test_creation_with_name(self) -> None:
        inst = Institution(name="Test University", abbreviation="TU")
        assert inst.name == "Test University"
        assert inst.abbreviation == "TU"
        assert inst.is_active is True


class TestGroup:
    def test_creation(self) -> None:
        group = Group(group_number=1, expected_enrollment=30, modality="presential")
        assert group.group_number == 1
        assert group.expected_enrollment == 30
        assert isinstance(group.id, uuid.UUID)

    def test_default_priority(self) -> None:
        group = Group()
        assert group.priority == 2


class TestInstructor:
    def test_creation(self) -> None:
        instructor = Instructor(first_name="John", last_name="Smith", employee_code="DS001")
        assert instructor.first_name == "John"
        assert isinstance(instructor.id, uuid.UUID)

    def test_default_active(self) -> None:
        instructor = Instructor()
        assert instructor.is_active is True

    def test_ids_are_unique(self) -> None:
        a = Instructor()
        b = Instructor()
        assert a.id != b.id
