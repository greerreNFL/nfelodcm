"""
Tests for assignment registry
"""
import pytest

from nfelodcm.nfelodcm.Engine.Assignments.assignment import (
    assignments as assignment_registry,
    assign,
    assignment_columns_added
)


class TestAssignmentRegistry:
    def test_all_registered_assignments_callable(self):
        """Every func in registry is callable"""
        for name, entry in assignment_registry.items():
            assert callable(entry['func']), (
                'Assignment "{0}" func is not callable'.format(name)
            )

    def test_assignment_columns_added_returns_list(self):
        """Returns list of tuples"""
        for name in assignment_registry:
            cols = assignment_columns_added(name)
            assert isinstance(cols, list)
            for col in cols:
                assert isinstance(col, tuple)
                assert len(col) == 2

    def test_unknown_assignment_raises(self):
        """Unregistered name raises KeyError"""
        with pytest.raises(KeyError):
            assign(None, 'nonexistent_assignment_name')
