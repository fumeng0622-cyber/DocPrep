
import re

from knowledge_schema import KnowledgeChunk


SENTENCE_PATTERN = re.compile(
    r"[^。！？!?；;\n]+[。！？!?；;]?|\n"
)


def validate_parameters(max_chars, overlap):
    """检查分块参数是否有效。"""

    if max_chars <= 0:
        raise ValueError("max_chars 必须大于 0")

    if overlap < 0 or overlap >= max_chars:
        raise ValueError(
            "overlap 必须大于等于 0 且小于 max_chars"
        )


def split_into_sentences(text):
    """拆分句子，并保留原始标点和换行符。"""

    sentences = SENTENCE_PATTERN.findall(text)

    if "".join(sentences) != text:
        return [text]

    return sentences


def get_sentence_overlap(text, overlap, available):
    """
    尽量从上一块末尾提取完整句子作为重叠内容。

    overlap：希望保留的最大重叠字符数
    available：下一块可用于重叠的字符数
    """

    limit = min(overlap, available)

    if limit <= 0:
        return ""

    sentences = split_into_sentences(text)

    selected = []
    total_length = 0

    for sentence in reversed(sentences):
        sentence_length = len(sentence)

        if total_length + sentence_length > limit:
            break

        selected.insert(0, sentence)
        total_length += sentence_length

    return "".join(selected)


def split_long_text(text, max_chars=800, overlap=100):
    """
    拆分超长文本。

    优先在句子边界拆分；
    尽量使用完整句子作为重叠内容；
    超长单句按字符拆分。
    """

    validate_parameters(max_chars, overlap)

    if len(text) <= max_chars:
        return [text]

    sentences = split_into_sentences(text)

    result = []
    current = ""

    for sentence in sentences:

        # 情况一：普通句子
        if len(sentence) <= max_chars:

            if len(current) + len(sentence) <= max_chars:
                current += sentence
                continue

            # 当前块放不下完整句子，先保存
            if current:
                result.append(current)

            overlap_text = get_sentence_overlap(
                current,
                overlap,
                max_chars - len(sentence),
            )

            current = overlap_text + sentence
            continue

        # 情况二：单句本身超过最大长度
        # 先保存之前的内容
        if current:
            result.append(current)
            current = ""

        start = 0

        while start < len(sentence):
            remaining = len(sentence) - start

            # 剩余内容可以放入当前块
            if len(current) + remaining <= max_chars:
                current += sentence[start:]
                break

            available = max_chars - len(current)

            piece = sentence[start:start + available]
            current += piece
            start += len(piece)

            result.append(current)

            # 单句内部无法保证完整句子重叠，
            # 因此保留字符级重叠
            current = (
                current[-overlap:]
                if overlap
                else ""
            )

    if current:
        result.append(current)

    return result


def build_chunks(chunks, max_chars=800, overlap=100):
    """
    根据章节和长度合并知识片段。

    1. 同一章节下的相邻正文可以合并。
    2. 遇到标题时停止合并。
    3. 表格等特殊内容单独保留。
    4. 超长正文进行拆分。
    """

    validate_parameters(max_chars, overlap)

    result = []
    buffer = []

    current_section = None
    current_subsection = None
    current_source = None

    def flush_buffer():
        """将暂存的正文保存为知识块。"""

        if not buffer:
            return

        first = buffer[0]

        content = "\n".join(
            item.content for item in buffer
        )

        pieces = split_long_text(
            content,
            max_chars=max_chars,
            overlap=overlap,
        )

        for piece in pieces:
            metadata = first.metadata.copy()

            metadata["element_type"] = "merged_text"
            metadata["paragraph_count"] = len(buffer)

            result.append(
                KnowledgeChunk(
                    content=piece,
                    source_file=first.source_file,
                    source_type=first.source_type,
                    title=first.title,
                    page_number=first.page_number,
                    section=first.section,
                    metadata=metadata,
                )
            )

        buffer.clear()

    for chunk in chunks:

        heading_level = chunk.metadata.get(
            "heading_level"
        )

        element_type = chunk.metadata.get(
            "element_type"
        )

        subsection = chunk.metadata.get(
            "subsection"
        )

        # 标题单独保留
        if heading_level is not None:
            flush_buffer()
            result.append(chunk)

            current_section = None
            current_subsection = None
            current_source = None
            continue

        # 表格等特殊内容单独保留
        if element_type != "paragraph":
            flush_buffer()
            result.append(chunk)

            current_section = None
            current_subsection = None
            current_source = None
            continue

        source = (
            chunk.source_file,
            chunk.source_type,
        )

        section_changed = (
            chunk.section != current_section
            or subsection != current_subsection
            or source != current_source
        )

        if buffer and section_changed:
            flush_buffer()

        current_length = sum(
            len(item.content)
            for item in buffer
        )

        separator_length = len(buffer)

        new_length = (
            current_length
            + separator_length
            + len(chunk.content)
        )

        if buffer and new_length > max_chars:
            flush_buffer()

        buffer.append(chunk)

        current_section = chunk.section
        current_subsection = subsection
        current_source = source

    flush_buffer()

    return result
