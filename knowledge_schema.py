
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class KnowledgeChunk:
    """
    统一的知识片段结构。

    不同格式的文件经过解析后，
    最终都可以转换成这种结构。
    """

    content: str
    source_file: str
    source_type: str

    title: str | None = None
    page_number: int | None = None
    section: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """将知识片段转换为字典，方便后续导出 JSON。"""
        return asdict(self)


def validate_chunk(chunk: KnowledgeChunk) -> None:
    """检查知识片段是否具备最基本的有效信息。"""

    if not chunk.content.strip():
        raise ValueError("知识片段内容不能为空。")

    if not chunk.source_file.strip():
        raise ValueError("来源文件名不能为空。")

    if not chunk.source_type.strip():
        raise ValueError("文件类型不能为空。")

    if chunk.page_number is not None and chunk.page_number < 1:
        raise ValueError("页码必须大于或等于 1。")
