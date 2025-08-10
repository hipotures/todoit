"""
Unit tests for tag color system and 12-color limit
Tests automatic color assignment, limit enforcement, and display functionality
"""
import pytest
from core.manager import TodoManager
from core.models import ListTag


class TestTagColorSystem:
    """Test suite for tag color system with 12-color limit"""

    def test_dynamic_color_assignment_sequence(self, manager):
        """Test that tags get colors assigned dynamically by alphabetical position"""
        expected_colors = [
            'red', 'green', 'blue', 'yellow', 'orange', 'purple', 
            'cyan', 'magenta', 'pink', 'grey', 'bright_green', 'bright_red'
        ]
        
        # Create tags in non-alphabetical order to test dynamic assignment
        tag_names = [f"tag_{i:02d}" for i in range(12)]
        created_tags = []
        
        for i, tag_name in enumerate(tag_names):
            tag = manager.create_tag(tag_name)
            created_tags.append(tag)
        
        # Get all tags - should be colored by alphabetical position
        all_tags = manager.get_all_tags()
        sorted_tags = sorted(all_tags, key=lambda x: x.name)
        
        # Verify colors match alphabetical order
        for i, tag in enumerate(sorted_tags):
            expected_color = expected_colors[i]
            assert tag.color == expected_color, f"Tag {tag.name} at position {i} should have color {expected_color}, got {tag.color}"
        
        # Verify all 12 tags created successfully
        assert len(all_tags) == 12
        
        # Verify all colors are unique
        colors = [tag.color for tag in all_tags]
        assert len(set(colors)) == 12, "All 12 colors should be unique"

    def test_12_tag_limit_enforcement(self, manager):
        """Test that 13th tag creation fails with appropriate error"""
        # Create 12 tags first
        for i in range(12):
            manager.create_tag(f"tag_{i}")
        
        # Verify 12 tags exist
        all_tags = manager.get_all_tags()
        assert len(all_tags) == 12
        
        # Try to create 13th tag - should fail
        with pytest.raises(ValueError, match="Maximum number of tags reached \\(12\\)"):
            manager.create_tag("tag_13")
        
        # Verify still only 12 tags
        all_tags_after = manager.get_all_tags()
        assert len(all_tags_after) == 12

    def test_explicit_color_override(self, manager):
        """Test that dynamic system overrides colors during retrieval"""
        # Create tag with explicit color - stored in database as blue
        tag = manager.create_tag("custom_tag", color="blue")
        # During creation, explicit color is stored
        assert tag.color == "blue"
        
        # Create second tag
        next_tag = manager.create_tag("auto_tag")
        
        # But when getting all tags, dynamic system calculates colors by alphabetical position
        all_tags = manager.get_all_tags()
        tag_colors = {t.name: t.color for t in all_tags}
        # Dynamic system assigns colors alphabetically regardless of stored color
        assert tag_colors["auto_tag"] == "red"      # First alphabetically (index 0)
        assert tag_colors["custom_tag"] == "green"  # Second alphabetically (index 1)

    def test_color_validation_with_underscores(self, manager):
        """Test that bright_green and bright_red colors are valid"""
        # These should work without validation errors
        tag1 = manager.create_tag("bright_tag1", color="bright_green")
        assert tag1.color == "bright_green"
        
        tag2 = manager.create_tag("bright_tag2", color="bright_red")
        assert tag2.color == "bright_red"

    def test_invalid_color_fallback(self, manager):
        """Test that invalid colors fallback to blue"""
        tag = manager.create_tag("invalid_color_tag", color="invalid_color")
        assert tag.color == "blue"

    def test_color_assignment_after_deletion(self, manager):
        """Test dynamic color assignment behavior after tag deletion"""
        # Create 3 tags
        tag1 = manager.create_tag("tag1")  
        tag2 = manager.create_tag("tag2")  
        tag3 = manager.create_tag("tag3")  
        
        # With dynamic system, colors are based on alphabetical order
        # Alphabetical: tag1, tag2, tag3 -> red, green, blue
        initial_tags = manager.get_all_tags()
        initial_colors = {t.name: t.color for t in initial_tags}
        assert initial_colors["tag1"] == "red"    # Index 0
        assert initial_colors["tag2"] == "green"  # Index 1
        assert initial_colors["tag3"] == "blue"   # Index 2
        
        # Delete middle tag
        manager.delete_tag("tag2")
        
        # Remaining tags shift colors: tag1, tag3 -> red, green
        remaining_tags = manager.get_all_tags()
        remaining_colors = {t.name: t.color for t in remaining_tags}
        assert remaining_colors["tag1"] == "red"   # Still index 0
        assert remaining_colors["tag3"] == "green" # Shifted to index 1
        
        # Create new tag - alphabetical position determines color
        tag4 = manager.create_tag("tag4")
        all_tags = manager.get_all_tags()
        final_colors = {t.name: t.color for t in all_tags}
        # Final order: tag1, tag3, tag4 -> red, green, blue
        assert final_colors["tag1"] == "red"
        assert final_colors["tag3"] == "green" 
        assert final_colors["tag4"] == "blue"

    def test_list_tags_display_formatting(self, manager):
        """Test that list tags can be formatted for display"""
        # Create list and tags
        todo_list = manager.create_list("test_list", "Test List")
        tag1 = manager.create_tag("tag1")  # red
        tag2 = manager.create_tag("tag2")  # green
        
        # Add tags to list
        manager.add_tag_to_list("test_list", "tag1")
        manager.add_tag_to_list("test_list", "tag2")
        
        # Get tags for list
        list_tags = manager.get_tags_for_list("test_list")
        assert len(list_tags) == 2
        
        # Test that colors are accessible for display formatting
        colors = [tag.color for tag in list_tags]
        assert "red" in colors
        assert "green" in colors

    def test_duplicate_tag_creation_fails(self, manager):
        """Test that creating duplicate tags fails appropriately"""
        manager.create_tag("duplicate_tag")
        
        with pytest.raises(ValueError, match="Tag 'duplicate_tag' already exists"):
            manager.create_tag("duplicate_tag")

    def test_dynamic_color_calculation_edge_cases(self, manager):
        """Test dynamic color calculation with edge cases"""
        # Test with empty database
        all_tags = manager.get_all_tags()
        assert len(all_tags) == 0
        
        # Create tags and test dynamic color assignment
        tag1 = manager.create_tag("zebra")  # Will be last alphabetically
        tag2 = manager.create_tag("alpha")  # Will be first alphabetically
        tag3 = manager.create_tag("beta")   # Will be second alphabetically
        
        # Get all tags and verify colors by alphabetical position
        all_tags = manager.get_all_tags()
        tag_colors = {t.name: t.color for t in all_tags}
        
        assert tag_colors["alpha"] == "red"    # Index 0 (first alphabetically)
        assert tag_colors["beta"] == "green"   # Index 1 (second alphabetically) 
        assert tag_colors["zebra"] == "blue"   # Index 2 (third alphabetically)

    def test_all_12_colors_are_valid_rich_colors(self, manager):
        """Test that all 12 defined colors are valid Rich color names"""
        expected_colors = [
            'red', 'green', 'blue', 'yellow', 'orange', 'purple', 
            'cyan', 'magenta', 'pink', 'grey', 'bright_green', 'bright_red'
        ]
        
        # Create tags with each color explicitly
        for i, color in enumerate(expected_colors):
            tag = manager.create_tag(f"color_test_{i}", color=color)
            assert tag.color == color
            
        # Verify all colors pass validation
        all_tags = manager.get_all_tags()
        assert len(all_tags) == 12
        
        colors = [tag.color for tag in all_tags]
        for expected_color in expected_colors:
            assert expected_color in colors

    def test_tag_limit_message_accuracy(self, manager):
        """Test that error message accurately reflects the 12 tag limit"""
        # Fill up to limit
        for i in range(12):
            manager.create_tag(f"tag_{i}")
            
        # Test error message contains correct number
        try:
            manager.create_tag("overflow_tag")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            error_msg = str(e)
            assert "12" in error_msg
            assert "Maximum number of tags reached" in error_msg
            assert "distinct colors" in error_msg