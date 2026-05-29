"""Tests for wod.core.types — enums and split templates."""

from __future__ import annotations

from wod.core.types import (
    SPLIT_TEMPLATES,
    EffortType,
    ExperienceLevel,
    MuscleGroup,
    SplitType,
)


class TestEnums:
    """Verify enum values and membership."""

    def test_experience_levels(self) -> None:
        assert len(ExperienceLevel) == 3
        assert ExperienceLevel("beginner") == ExperienceLevel.BEGINNER

    def test_muscle_groups(self) -> None:
        assert len(MuscleGroup) == 9
        assert MuscleGroup("chest") == MuscleGroup.CHEST

    def test_effort_types(self) -> None:
        assert len(EffortType) == 2
        assert EffortType("compound") == EffortType.COMPOUND

    def test_split_types(self) -> None:
        assert len(SplitType) == 3
        assert SplitType("full_body") == SplitType.FULL_BODY


class TestSplitTemplates:
    """Verify the split template definitions."""

    def test_all_splits_have_templates(self) -> None:
        for split in SplitType:
            assert split in SPLIT_TEMPLATES

    def test_full_body_covers_all_groups(self) -> None:
        template = SPLIT_TEMPLATES[SplitType.FULL_BODY]
        assert len(template) == 1
        all_groups = set(template[0])
        assert all_groups == set(MuscleGroup)

    def test_upper_lower_has_two_days(self) -> None:
        template = SPLIT_TEMPLATES[SplitType.UPPER_LOWER]
        assert len(template) == 2

    def test_ppl_has_three_days(self) -> None:
        template = SPLIT_TEMPLATES[SplitType.PUSH_PULL_LEGS]
        assert len(template) == 3

    def test_all_groups_covered_in_ppl(self) -> None:
        template = SPLIT_TEMPLATES[SplitType.PUSH_PULL_LEGS]
        all_groups_in_ppl: set[MuscleGroup] = set()
        for day_groups in template:
            all_groups_in_ppl.update(day_groups)
        assert all_groups_in_ppl == set(MuscleGroup)

    def test_all_groups_covered_in_upper_lower(self) -> None:
        template = SPLIT_TEMPLATES[SplitType.UPPER_LOWER]
        all_groups: set[MuscleGroup] = set()
        for day_groups in template:
            all_groups.update(day_groups)
        assert all_groups == set(MuscleGroup)
