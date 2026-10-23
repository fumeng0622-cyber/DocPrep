
import re

from knowledge_schema import KnowledgeChunk


# 一级标题：一、总体要求
SECTION_PATTERN = re.compile(
    r"^[一二三四五六七八九十百]+、\s*.+$"
)

# 二级标题：（一）公文大标题
SUBSECTION_PATTERN = re.compile(
    r"^[（(]\s*[一二三四五六七八九十百]+\s*[）)]\s*.+$"
)

# 一级标题：第一章 Python 基础
CHAPTER_PATTERN = re.compile(
    r"^第[一二三四五六七八九十百千\d]+章\s+.+$"
)

# 数字标题：1.1 变量、1.1.1 变量命名
NUMBERED_HEADING_PATTERN = re.compile(
    r"^(\d+(?:\.\d+)+)[.、]?\s+.+$"
)


def detect_heading_level(chunk):
    """
    判断知识片段是否为标题。

    返回：
    0：文档主标题
    1：一级标题
    2：二级标题
    None：普通正文
    """

    if chunk.metadata.get("element_type") != "paragraph":
        return None

    content = chunk.content.strip()
    style = chunk.metadata.get("paragraph_style", "")
    normalized_style = style.strip().lower()

    # 优先识别 Word 文档主标题样式
    if normalized_style in ("title", "标题"):
        return 0

    # 识别明确的标题编号
    if SECTION_PATTERN.match(content):
        return 1

    if SUBSECTION_PATTERN.match(content):
        return 2

    if CHAPTER_PATTERN.match(content):
        return 1

    # 数字编号标题
    match = NUMBERED_HEADING_PATTERN.match(content)

    if match:
        number = match.group(1)
        depth = len(number.split("."))

        if depth == 2:
            return 2

        # 第一版暂时把三级及更深标题归入二级
        if depth >= 3:
            return 2

    # 识别 Word 章节标题样式
    if normalized_style in ("heading 1", "标题 1"):
        return 1

    if normalized_style in ("heading 2", "标题 2"):
        return 2

    return None


def attach_section_context(chunks):
    """为知识片段添加文档标题、一级章节和二级标题信息。"""

    result = []

    current_title = None
    current_section = None
    current_subsection = None

    for chunk in chunks:
        content = chunk.content.strip()
        heading_level = detect_heading_level(chunk)

        if heading_level == 0:
            current_title = content
            current_section = None
            current_subsection = None

        elif heading_level == 1:
            current_section = content
            current_subsection = None

        elif heading_level == 2:
            current_subsection = content

        new_metadata = chunk.metadata.copy()
        new_metadata["subsection"] = current_subsection
        new_metadata["heading_level"] = heading_level

        new_chunk = KnowledgeChunk(
            content=chunk.content,
            source_file=chunk.source_file,
            source_type=chunk.source_type,
            title=current_title or chunk.title,
            page_number=chunk.page_number,
            section=current_section,
            metadata=new_metadata,
        )

        result.append(new_chunk)

    return result
