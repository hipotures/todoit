"""
TODOIT MCP - Pydantic Models
Data models for TODO list management system
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class ListType(str, Enum):
    """Types of TODO lists"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    LINKED = "linked"


class ListStatus(str, Enum):
    """Status of TODO lists"""
    ACTIVE = "active"
    ARCHIVED = "archived"


class ItemStatus(str, Enum):
    """Status of TODO items"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RelationType(str, Enum):
    """Types of relations between lists"""
    DEPENDENCY = "dependency"
    PARENT = "parent"
    RELATED = "related"
    PROJECT = "project"


class HistoryAction(str, Enum):
    """Types of history actions"""
    CREATED = "created"
    UPDATED = "updated"
    COMPLETED = "completed" 
    FAILED = "failed"
    DELETED = "deleted"
    STATES_CLEARED = "states_cleared"


class DependencyType(str, Enum):
    """Types of cross-list item dependencies - Phase 2"""
    BLOCKS = "blocks"      # Required item blocks dependent item
    REQUIRES = "requires"  # Dependent item requires required item
    RELATED = "related"    # Informational relationship


class CompletionStates(BaseModel):
    """Multi-state completion tracking for complex tasks"""
    states: Dict[str, bool] = Field(default_factory=dict)
    
    def add_state(self, state_name: str, completed: bool = False) -> None:
        """Add or update a completion state"""
        self.states[state_name] = completed
    
    def is_fully_completed(self) -> bool:
        """Check if all states are completed"""
        return all(self.states.values()) if self.states else False
    
    def is_partially_completed(self) -> bool:
        """Check if any state is completed"""
        return any(self.states.values()) if self.states else False
    
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if not self.states:
            return 0.0
        completed_count = sum(1 for state in self.states.values() if state)
        return (completed_count / len(self.states)) * 100


class TodoListBase(BaseModel):
    """Base model for TODO lists"""
    list_key: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    list_type: ListType = ListType.SEQUENTIAL
    status: ListStatus = ListStatus.ACTIVE
    parent_list_id: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('list_key')
    def validate_list_key(cls, v):
        """Validate list_key format"""
        if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError('list_key must contain only alphanumeric characters, underscores, hyphens, and dots')
        return v


class TodoListCreate(TodoListBase):
    """Model for creating TODO lists"""
    pass


class TodoListUpdate(BaseModel):
    """Model for updating TODO lists"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    list_type: Optional[ListType] = None
    status: Optional[ListStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class TodoList(TodoListBase):
    """Complete TODO list model"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "list_key": self.list_key,
            "title": self.title,
            "description": self.description,
            "list_type": self.list_type,
            "parent_list_id": self.parent_list_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class TodoItemBase(BaseModel):
    """Base model for TODO items"""
    item_key: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., max_length=1000)
    position: int = Field(..., ge=0)
    status: ItemStatus = ItemStatus.PENDING
    completion_states: Optional[Dict[str, Any]] = Field(default_factory=dict)
    parent_item_id: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('item_key')
    def validate_item_key(cls, v):
        """Validate item_key format"""
        if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError('item_key must contain only alphanumeric characters, underscores, hyphens, and dots')
        return v


class TodoItemCreate(TodoItemBase):
    """Model for creating TODO items"""
    list_id: int


class TodoItemUpdate(BaseModel):
    """Model for updating TODO items"""
    content: Optional[str] = Field(None, max_length=1000)
    position: Optional[int] = Field(None, ge=0)
    status: Optional[ItemStatus] = None
    completion_states: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class TodoItem(TodoItemBase):
    """Complete TODO item model"""
    id: int
    list_id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "list_id": self.list_id,
            "item_key": self.item_key,
            "content": self.content,
            "position": self.position,
            "status": self.status,
            "completion_states": self.completion_states,
            "parent_item_id": self.parent_item_id,
            "metadata": self.metadata,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def get_completion_metadata(self) -> Dict[str, Any]:
        """Get completion metadata"""
        return self.completion_states or {}


class ListRelationBase(BaseModel):
    """Base model for list relations"""
    source_list_id: int
    target_list_id: int
    relation_type: RelationType
    relation_key: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('target_list_id')
    def validate_different_lists(cls, v, info):
        """Ensure source and target are different lists"""
        if info.data and 'source_list_id' in info.data and v == info.data['source_list_id']:
            raise ValueError('source_list_id and target_list_id must be different')
        return v


class ListRelationCreate(ListRelationBase):
    """Model for creating list relations"""
    pass


class ListRelation(ListRelationBase):
    """Complete list relation model"""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "source_list_id": self.source_list_id,
            "target_list_id": self.target_list_id,
            "relation_type": self.relation_type,
            "relation_key": self.relation_key,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class ListPropertyBase(BaseModel):
    """Base model for list properties (key-value storage)"""
    list_id: int
    property_key: str = Field(..., min_length=1, max_length=100)
    property_value: str = Field(..., max_length=2000)
    
    @field_validator('property_key')
    def validate_property_key(cls, v):
        """Validate property_key format"""
        import re
        
        # Allow alphanumeric, underscores, hyphens, dots, and colons for namespacing
        if not re.match(r'^[a-zA-Z0-9_\-.:]+$', v):
            raise ValueError('property_key must contain only alphanumeric characters, underscores, hyphens, dots, and colons')
        
        if len(v) < 1 or len(v) > 100:
            raise ValueError('property_key must be between 1 and 100 characters')
        
        # Prevent reserved keys
        reserved_keys = {'id', 'created_at', 'updated_at', 'list_id'}
        if v.lower() in reserved_keys:
            raise ValueError(f'property_key "{v}" is reserved')
        
        return v
    
    @field_validator('property_value')
    def validate_property_value(cls, v):
        """Validate property_value content and prevent XSS"""
        if len(v) > 2000:
            raise ValueError('property_value cannot exceed 2000 characters')
        
        # Basic XSS prevention for web contexts
        dangerous_patterns = ['<script>', 'javascript:', 'onload=', 'onerror=', 'onclick=', 'onmouseover=']
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f'property_value contains potentially dangerous content: {pattern}')
        
        # Check for HTML injection attempts
        if '<' in v and '>' in v:
            import re
            # Allow simple formatting tags but block script tags
            allowed_tags = r'</?(?:b|i|u|em|strong|br|p)/?>'
            if re.search(r'<(?!/?(?:b|i|u|em|strong|br|p)/?)[^>]*>', v, re.IGNORECASE):
                raise ValueError('property_value contains potentially dangerous HTML tags')
        
        return v


class ListPropertyCreate(ListPropertyBase):
    """Model for creating list properties"""
    pass


class ListPropertyUpdate(BaseModel):
    """Model for updating list properties"""
    property_value: Optional[str] = Field(None, max_length=2000)


class ListProperty(ListPropertyBase):
    """Complete list property model"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "list_id": self.list_id,
            "property_key": self.property_key,
            "property_value": self.property_value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class TodoHistoryBase(BaseModel):
    """Base model for TODO history"""
    item_id: Optional[int] = None
    list_id: Optional[int] = None
    action: HistoryAction
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    user_context: str = Field(default="system")


class TodoHistoryCreate(TodoHistoryBase):
    """Model for creating history entries"""
    pass


class TodoHistory(TodoHistoryBase):
    """Complete history entry model"""
    id: int
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "item_id": self.item_id,
            "list_id": self.list_id,
            "action": self.action,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "user_context": self.user_context,
            "timestamp": self.timestamp.isoformat()
        }


class ProgressStats(BaseModel):
    """Model for progress statistics"""
    total: int = 0
    completed: int = 0
    in_progress: int = 0
    pending: int = 0
    failed: int = 0
    completion_percentage: float = 0.0
    
    # Phase 3: Enhanced progress tracking
    blocked: int = 0  # Items blocked by cross-list dependencies
    available: int = 0  # Items available to start (not blocked)
    root_items: int = 0  # Count of root items (no parent)
    subtasks: int = 0  # Count of subtasks (has parent)
    hierarchy_depth: int = 0  # Maximum hierarchy depth
    dependency_count: int = 0  # Total cross-list dependencies
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "total": self.total,
            "completed": self.completed,
            "in_progress": self.in_progress,
            "pending": self.pending,
            "failed": self.failed,
            "completion_percentage": self.completion_percentage,
            "blocked": self.blocked,
            "available": self.available,
            "root_items": self.root_items,
            "subtasks": self.subtasks,
            "hierarchy_depth": self.hierarchy_depth,
            "dependency_count": self.dependency_count
        }


class BulkOperationResult(BaseModel):
    """Model for bulk operation results"""
    success: bool
    affected_count: int
    errors: List[str] = Field(default_factory=list)
    items: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "affected_count": self.affected_count,
            "errors": self.errors,
            "items": self.items
        }


# ===== ITEM PROPERTIES MODELS =====

class ItemPropertyBase(BaseModel):
    """Base model for item properties"""
    property_key: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    property_value: str = Field(..., min_length=1, max_length=1000)


class ItemPropertyCreate(ItemPropertyBase):
    """Model for creating item properties"""
    item_id: int


class ItemPropertyUpdate(BaseModel):
    """Model for updating item properties"""
    property_value: str = Field(..., min_length=1, max_length=1000)


class ItemProperty(ItemPropertyBase):
    """Complete item property model"""
    id: int
    item_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "item_id": self.item_id,
            "property_key": self.property_key,
            "property_value": self.property_value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# ===== PHASE 2: CROSS-LIST DEPENDENCIES MODELS =====

class ItemDependencyBase(BaseModel):
    """Base model for cross-list item dependencies"""
    dependent_item_id: int = Field(..., gt=0, description="ID of item that depends on another")
    required_item_id: int = Field(..., gt=0, description="ID of item that is required")
    dependency_type: DependencyType = Field(default=DependencyType.BLOCKS)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('dependent_item_id', 'required_item_id')
    def validate_item_ids(cls, v):
        """Validate item IDs are positive integers"""
        if v <= 0:
            raise ValueError('Item IDs must be positive integers')
        return v
    
    @field_validator('metadata')  
    def validate_metadata(cls, v):
        """Validate metadata content"""
        if v is None:
            return {}
        
        # Limit metadata size
        import json
        if len(json.dumps(v)) > 1000:
            raise ValueError('Metadata too large (max 1000 characters when serialized)')
        
        return v


class ItemDependencyCreate(ItemDependencyBase):
    """Model for creating item dependencies"""
    
    @field_validator('required_item_id')
    def validate_not_self_dependency(cls, v, info):
        """Prevent self-dependencies"""
        if info.data and 'dependent_item_id' in info.data and v == info.data['dependent_item_id']:
            raise ValueError('Item cannot depend on itself')
        return v


class ItemDependency(ItemDependencyBase):
    """Complete item dependency model"""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "dependent_item_id": self.dependent_item_id,
            "required_item_id": self.required_item_id,
            "dependency_type": self.dependency_type,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class DependencyGraph(BaseModel):
    """Model for dependency graph visualization"""
    lists: List[Dict[str, Any]] = Field(default_factory=list)
    items: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "lists": self.lists,
            "items": self.items,
            "dependencies": self.dependencies
        }


class BlockedItemsResult(BaseModel):
    """Model for blocked items query results"""
    item_id: int
    item_key: str
    content: str
    list_key: str
    blockers: List[Dict[str, Any]] = Field(default_factory=list)
    is_blocked: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "item_id": self.item_id,
            "item_key": self.item_key,
            "content": self.content,
            "list_key": self.list_key,
            "blockers": self.blockers,
            "is_blocked": self.is_blocked
        }


# ===== LIST TAGS MODELS =====

class ListTagBase(BaseModel):
    """Base model for list tags"""
    name: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    color: str = Field(default='blue', max_length=20, pattern=r'^[a-zA-Z0-9_#\s]+$')
    
    @field_validator('name')
    def validate_tag_name(cls, v):
        """Validate tag name format"""
        if v.lower() in ['all', 'none', 'null', 'undefined']:
            raise ValueError('Tag name cannot be a reserved word')
        return v.lower()  # Normalize to lowercase
    
    @field_validator('color')
    def validate_color(cls, v):
        """Validate color format - 12 distinct colors for visual recognition"""
        valid_colors = [
            'red', 'green', 'blue', 'yellow', 'orange', 'purple', 
            'cyan', 'magenta', 'pink', 'grey', 'bright_green', 'bright_red'
        ]
        if not (v.lower() in valid_colors or v.startswith('#')):
            return 'blue'  # Default fallback
        return v.lower()


class ListTagCreate(ListTagBase):
    """Model for creating list tags"""
    pass


class ListTag(ListTagBase):
    """Complete list tag model"""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "created_at": self.created_at.isoformat()
        }


class ListTagAssignmentBase(BaseModel):
    """Base model for list tag assignments"""
    list_id: int = Field(..., gt=0)
    tag_id: int = Field(..., gt=0)
    
    @field_validator('list_id', 'tag_id')
    def validate_ids(cls, v):
        """Validate IDs are positive"""
        if v <= 0:
            raise ValueError('IDs must be positive integers')
        return v


class ListTagAssignmentCreate(ListTagAssignmentBase):
    """Model for creating list tag assignments"""
    pass


class ListTagAssignment(ListTagAssignmentBase):
    """Complete list tag assignment model"""
    id: int
    assigned_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "list_id": self.list_id,
            "tag_id": self.tag_id,
            "assigned_at": self.assigned_at.isoformat()
        }