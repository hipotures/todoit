"""
Unit tests for dynamic tag color system based on alphabetical sorting
Tests real-time color assignment, deletion shifts, and edge cases
"""

import pytest
from core.manager import TodoManager


class TestDynamicTagColors:
    """Test suite for dynamic tag color assignment system"""

    def test_alphabetical_color_assignment(self, manager):
        """Test that tags get colors assigned alphabetically"""
        # Create tags in non-alphabetical order
        tag_c = manager.create_tag("charlie")
        tag_a = manager.create_tag("alpha")
        tag_b = manager.create_tag("beta")

        # Get all tags - should be colored by alphabetical position
        all_tags = manager.get_all_tags()
        tag_dict = {tag.name: tag.color for tag in all_tags}

        # Check alphabetical color assignment
        assert tag_dict["alpha"] == "red"  # Index 0
        assert tag_dict["beta"] == "green"  # Index 1
        assert tag_dict["charlie"] == "blue"  # Index 2

    def test_color_shift_after_deletion(self, manager):
        """Test that colors shift when a tag is deleted"""
        # Create tags
        manager.create_tag("apple")
        manager.create_tag("banana")
        manager.create_tag("cherry")
        manager.create_tag("date")

        # Verify initial colors
        all_tags = manager.get_all_tags()
        initial_colors = {tag.name: tag.color for tag in all_tags}

        assert initial_colors["apple"] == "red"  # Index 0
        assert initial_colors["banana"] == "green"  # Index 1
        assert initial_colors["cherry"] == "blue"  # Index 2
        assert initial_colors["date"] == "yellow"  # Index 3

        # Delete first tag
        manager.delete_tag("apple")

        # Verify colors shifted
        remaining_tags = manager.get_all_tags()
        shifted_colors = {tag.name: tag.color for tag in remaining_tags}

        assert shifted_colors["banana"] == "red"  # Shifted to index 0
        assert shifted_colors["cherry"] == "green"  # Shifted to index 1
        assert shifted_colors["date"] == "blue"  # Shifted to index 2

    def test_dynamic_colors_in_list_tags(self, manager):
        """Test dynamic colors when getting tags for a specific list"""
        # Create list and tags
        todo_list = manager.create_list("test_list", "Test List")
        manager.create_tag("zebra")
        manager.create_tag("alpha")
        manager.create_tag("beta")

        # Add tags to list
        manager.add_tag_to_list("test_list", "zebra")
        manager.add_tag_to_list("test_list", "alpha")

        # Get tags for list - should have dynamic colors
        list_tags = manager.get_tags_for_list("test_list")
        tag_colors = {tag.name: tag.color for tag in list_tags}

        # Verify colors match alphabetical positions globally
        assert tag_colors["alpha"] == "red"  # First alphabetically in system
        assert tag_colors["zebra"] == "blue"  # Third alphabetically in system

    def test_12_color_cycling(self, manager):
        """Test that colors cycle after 12 tags"""
        # Create exactly 13 tags to test cycling
        tag_names = [f"tag_{i:02d}" for i in range(13)]

        # First 12 should work
        for i in range(12):
            manager.create_tag(tag_names[i])

        # 13th should fail due to limit
        with pytest.raises(ValueError, match="Maximum number of tags reached"):
            manager.create_tag(tag_names[12])

    def test_color_consistency_across_methods(self, manager):
        """Test that same tag gets same color from different methods"""
        # Create tags
        manager.create_tag("delta")
        manager.create_tag("alpha")
        manager.create_tag("gamma")

        # Create list and assign tag
        manager.create_list("color_test", "Color Test")
        manager.add_tag_to_list("color_test", "gamma")

        # Get color from get_all_tags()
        all_tags = manager.get_all_tags()
        gamma_color_all = next(tag.color for tag in all_tags if tag.name == "gamma")

        # Get color from get_tags_for_list()
        list_tags = manager.get_tags_for_list("color_test")
        gamma_color_list = next(tag.color for tag in list_tags if tag.name == "gamma")

        # Should be identical
        assert gamma_color_all == gamma_color_list
        assert (
            gamma_color_all == "blue"
        )  # gamma is 3rd alphabetically (alpha, delta, gamma)

    def test_empty_tag_list_handling(self, manager):
        """Test behavior with no tags"""
        # Should not crash
        all_tags = manager.get_all_tags()
        assert len(all_tags) == 0

        # List tags should also work
        manager.create_list("empty_test", "Empty Test")
        list_tags = manager.get_tags_for_list("empty_test")
        assert len(list_tags) == 0

    def test_single_tag_color_assignment(self, manager):
        """Test color assignment with only one tag"""
        tag = manager.create_tag("lonely")

        all_tags = manager.get_all_tags()
        assert len(all_tags) == 1
        assert all_tags[0].color == "red"  # First color
        assert all_tags[0].name == "lonely"

    def test_middle_tag_deletion_shift(self, manager):
        """Test deleting middle tag shifts colors correctly"""
        # Create 5 tags
        for i, name in enumerate(["alpha", "beta", "gamma", "delta", "epsilon"]):
            manager.create_tag(name)

        # Verify initial state - tags are sorted alphabetically
        initial_tags = manager.get_all_tags()
        initial_colors = {tag.name: tag.color for tag in initial_tags}

        # Alphabetical order: alpha, beta, delta, epsilon, gamma
        assert initial_colors["alpha"] == "red"  # Index 0
        assert initial_colors["beta"] == "green"  # Index 1
        assert initial_colors["delta"] == "blue"  # Index 2
        assert initial_colors["epsilon"] == "yellow"  # Index 3
        assert initial_colors["gamma"] == "orange"  # Index 4

        # Delete middle tag (delta - alphabetically 3rd)
        manager.delete_tag("delta")

        # Verify shift - remaining order: alpha, beta, epsilon, gamma
        remaining_tags = manager.get_all_tags()
        remaining_colors = {tag.name: tag.color for tag in remaining_tags}

        assert remaining_colors["alpha"] == "red"  # No change (index 0)
        assert remaining_colors["beta"] == "green"  # No change (index 1)
        assert (
            remaining_colors["epsilon"] == "blue"
        )  # Shifted from yellow to blue (index 2)
        assert (
            remaining_colors["gamma"] == "yellow"
        )  # Shifted from orange to yellow (index 3)

    def test_tag_name_sorting_case_insensitive(self, manager):
        """Test that tag sorting is consistent"""
        # Create tags with mixed case
        manager.create_tag("Zebra")
        manager.create_tag("alpha")
        manager.create_tag("Beta")

        all_tags = manager.get_all_tags()
        tag_colors = {tag.name: tag.color for tag in all_tags}

        # All tag names should be lowercase in system
        expected_names = ["alpha", "beta", "zebra"]  # Sorted alphabetically
        actual_names = sorted([tag.name for tag in all_tags])

        assert actual_names == expected_names

        # Colors should follow alphabetical order
        assert tag_colors["alpha"] == "red"  # Index 0
        assert tag_colors["beta"] == "green"  # Index 1
        assert tag_colors["zebra"] == "blue"  # Index 2

    def test_color_stability_within_session(self, manager):
        """Test that colors remain stable during a session"""
        # Create tags
        manager.create_tag("stable_1")
        manager.create_tag("stable_2")
        manager.create_tag("stable_3")

        # Get colors multiple times
        colors_1 = {tag.name: tag.color for tag in manager.get_all_tags()}
        colors_2 = {tag.name: tag.color for tag in manager.get_all_tags()}
        colors_3 = {tag.name: tag.color for tag in manager.get_all_tags()}

        # Should be identical
        assert colors_1 == colors_2 == colors_3

    def test_color_recalculation_performance(self, manager):
        """Test that color recalculation works with many tags"""
        # Create close to limit tags
        tag_names = [f"perf_tag_{i:02d}" for i in range(10)]

        for name in tag_names:
            manager.create_tag(name)

        # Should handle getting all tags efficiently
        all_tags = manager.get_all_tags()
        assert len(all_tags) == 10

        # Each tag should have a unique color
        colors = [tag.color for tag in all_tags]
        assert len(set(colors)) == 10  # All colors should be unique

        # Should follow expected color sequence
        expected_colors = [
            "red",
            "green",
            "blue",
            "yellow",
            "orange",
            "purple",
            "cyan",
            "magenta",
            "pink",
            "grey",
        ]

        sorted_tags = sorted(all_tags, key=lambda x: x.name)
        actual_colors = [tag.color for tag in sorted_tags]
        assert actual_colors == expected_colors

    def test_list_specific_tag_color_consistency(self, manager):
        """Test that list-specific tag queries return consistent colors"""
        # Create multiple lists and tags
        manager.create_list("list_a", "List A")
        manager.create_list("list_b", "List B")

        manager.create_tag("shared_tag")
        manager.create_tag("unique_tag_a")
        manager.create_tag("unique_tag_b")

        # Assign tags to lists
        manager.add_tag_to_list("list_a", "shared_tag")
        manager.add_tag_to_list("list_a", "unique_tag_a")
        manager.add_tag_to_list("list_b", "shared_tag")
        manager.add_tag_to_list("list_b", "unique_tag_b")

        # Get tags for each list
        tags_a = manager.get_tags_for_list("list_a")
        tags_b = manager.get_tags_for_list("list_b")

        # shared_tag should have same color in both lists
        shared_color_a = next(tag.color for tag in tags_a if tag.name == "shared_tag")
        shared_color_b = next(tag.color for tag in tags_b if tag.name == "shared_tag")

        assert shared_color_a == shared_color_b

        # Should match global color too
        all_tags = manager.get_all_tags()
        shared_color_global = next(
            tag.color for tag in all_tags if tag.name == "shared_tag"
        )

        assert shared_color_a == shared_color_global
