from enum import StrEnum


class StatusFilter(StrEnum):
    ALL = "all"
    PENDING = "pending"
    COMPLETED = "completed"


class PriorityFilter(StrEnum):
    ALL = "all"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DueFilter(StrEnum):
    ALL = "all"
    OVERDUE = "overdue"
    TODAY = "today"
    UPCOMING = "upcoming"
    NO_DATE = "noDate"


class SortField(StrEnum):
    TITLE = "title"
    PRIORITY = "priority"
    DUE_DATE = "dueDate"
    CREATED_AT = "createdAt"
    UPDATED_AT = "updatedAt"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"
