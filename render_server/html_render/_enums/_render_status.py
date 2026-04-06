from enum import StrEnum

class RenderStatus(StrEnum):
    """渲染状态"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"