from enum import Enum


class StatusFilter(str, Enum):
    ALL = "all"
    PENDING = "pending"
    COMPLETED = "completed"


class PriorityFilter(str, Enum):
    ALL = "all"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DueFilter(str, Enum):
    ALL = "all"
    OVERDUE = "overdue"
    TODAY = "today"
    UPCOMING = "upcoming"
    NO_DATE = "noDate"


class SortField(str, Enum):
    TITLE = "title"
    PRIORITY = "priority"
    DUE_DATE = "dueDate"
    CREATED_AT = "createdAt"
    UPDATED_AT = "updatedAt"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"