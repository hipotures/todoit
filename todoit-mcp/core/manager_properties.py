"""
TODOIT MCP - Properties Management Mixin
Collection of property management methods for TodoManager
"""

from typing import Dict, Optional, List, Any

from .models import ListProperty, ItemProperty


class PropertiesMixin:
    """Mixin containing property management methods for TodoManager"""

    def set_list_property(self, list_key: str, property_key: str, property_value: str) -> ListProperty:
        """Set a property for a list"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Create or update property
        property_data = {
            "list_id": db_list.id,
            "property_key": property_key,
            "property_value": property_value,
        }

        # Check if property already exists
        existing = self.db.get_list_property(db_list.id, property_key)
        if existing:
            # Update existing property
            db_property = self.db.update_list_property(existing.id, {"property_value": property_value})
        else:
            # Create new property
            db_property = self.db.create_list_property(property_data)

        return self._db_to_model(db_property, ListProperty)

    def get_list_property(self, list_key: str, property_key: str) -> Optional[str]:
        """Get a property value for a list"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get property
        db_property = self.db.get_list_property(db_list.id, property_key)
        return db_property.property_value if db_property else None

    def get_list_properties(self, list_key: str) -> Dict[str, str]:
        """Get all properties for a list as a dictionary"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get all properties
        db_properties = self.db.get_list_properties(db_list.id)
        
        # Convert to dictionary
        properties = {}
        for prop in db_properties:
            properties[prop.property_key] = prop.property_value
            
        return properties

    def delete_list_property(self, list_key: str, property_key: str) -> bool:
        """Delete a property from a list"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get the property
        db_property = self.db.get_list_property(db_list.id, property_key)
        if not db_property:
            return False

        # Delete property
        return self.db.delete_list_property(db_property.id)

    def set_item_property(self, list_key: str, item_key: str, property_key: str, property_value: str, parent_item_key: Optional[str] = None) -> ItemProperty:
        """Set a property for an item"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get parent item ID if specified
        parent_item_id = None
        if parent_item_key:
            parent_item = self.db.get_item_by_key(db_list.id, parent_item_key)
            if not parent_item:
                raise ValueError(f"Parent item '{parent_item_key}' not found in list '{list_key}'")
            parent_item_id = parent_item.id

        # Get the item
        db_item = self.db.get_item_by_key_and_parent(db_list.id, item_key, parent_item_id)
        if not db_item:
            if parent_item_key:
                raise ValueError(f"Item '{item_key}' not found under parent '{parent_item_key}' in list '{list_key}'")
            else:
                raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Create or update property
        property_data = {
            "item_id": db_item.id,
            "property_key": property_key,
            "property_value": property_value,
        }

        # Check if property already exists
        existing = self.db.get_item_property(db_item.id, property_key)
        if existing:
            # Update existing property
            db_property = self.db.update_item_property(existing.id, {"property_value": property_value})
        else:
            # Create new property
            db_property = self.db.create_item_property(property_data)

        return self._db_to_model(db_property, ItemProperty)

    def get_item_property(self, list_key: str, item_key: str, property_key: str, parent_item_key: Optional[str] = None) -> Optional[str]:
        """Get a property value for an item"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get parent item ID if specified
        parent_item_id = None
        if parent_item_key:
            parent_item = self.db.get_item_by_key(db_list.id, parent_item_key)
            if not parent_item:
                raise ValueError(f"Parent item '{parent_item_key}' not found in list '{list_key}'")
            parent_item_id = parent_item.id

        # Get the item
        db_item = self.db.get_item_by_key_and_parent(db_list.id, item_key, parent_item_id)
        if not db_item:
            if parent_item_key:
                raise ValueError(f"Item '{item_key}' not found under parent '{parent_item_key}' in list '{list_key}'")
            else:
                raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Get property
        db_property = self.db.get_item_property(db_item.id, property_key)
        return db_property.property_value if db_property else None