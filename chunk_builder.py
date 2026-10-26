
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
        if current:
            result.append(current)
            current = ""

        start = 0

        while start < len(sentence):
            remaining = len(sentence) - start

            if len(current) + remaining <= max_chars:
                current += sentence[start:]
                break

            available = max_chars - len(current)

            piece = sentence[start:start + available]
            current += piece
            start += len(piece)

            result.append(current)

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
    根据章节、内容类型和长度构建知识块。

    1. 同一章节下的相邻正文可以合并。
    2. 遇到标题时停止合并。
    3. 同一张表格的连续行可以合并。
    4. 不同表格和普通正文保持独立。
    5. 超长正文按句子拆分。
    6. 超长表格优先按完整行拆分并重复表头。
    """

    validate_parameters(max_chars, overlap)

    result = []
    buffer = []
    table_buffer = []

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

    def flush_table_buffer():
        """合并表格行；超长时按完整行拆分并重复表头。"""

        if not table_buffer:
            return

        first = table_buffer[0]

        total_content = "\n".join(
            item.content for item in table_buffer
        )

        # 每个元素保存：
        # (知识块文本, 实际行数, 是否包含部分行)
        table_pieces = []

        if len(total_content) <= max_chars:
            table_pieces.append(
                (total_content, len(table_buffer), False)
            )

        else:
            header_text = table_buffer[0].content
            data_rows = table_buffer[1:]

            # 表头本身过长时，无法在有限长度内
            # 同时保留完整表头和数据行。
            # 此时将整张表格按文本拆分，并明确标记。
            if len(header_text) >= max_chars:
                pieces = split_long_text(
                    total_content,
                    max_chars=max_chars,
                    overlap=0,
                )

                for piece in pieces:
                    table_pieces.append(
                        (piece, None, True)
                    )

            else:
                current_rows = [header_text]
                current_count = 1

                for row in data_rows:
                    row_text = row.content

                    # 当前块加上新行之后的长度
                    current_content = "\n".join(
                        current_rows
                    )

                    new_length = (
                        len(current_content)
                        + 1
                        + len(row_text)
                    )

                    if new_length <= max_chars:
                        current_rows.append(row_text)
                        current_count += 1
                        continue

                    # 当前块已经包含数据行，先保存
                    if current_count > 1:
                        table_pieces.append(
                            (
                                "\n".join(current_rows),
                                current_count,
                                False,
                            )
                        )

                    # 新块重新加入表头
                    current_rows = [header_text]
                    current_count = 1

                    # 检查单独一行能否与表头放在一起
                    row_with_header = (
                        header_text + "\n" + row_text
                    )

                    if len(row_with_header) <= max_chars:
                        current_rows.append(row_text)
                        current_count += 1

                    else:
                        # 单行本身过长，无法完整放入知识块。
                        # 将该行拆成多个片段，每块保留表头。
                        available = (
                            max_chars
                            - len(header_text)
                            - 1
                        )

                        start = 0

                        while start < len(row_text):
                            row_piece = row_text[
                                start:start + available
                            ]

                            table_pieces.append(
                                (
                                    header_text + "\n" + row_piece,
                                    None,
                                    True,
                                )
                            )

                            start += len(row_piece)

                # 保存最后尚未写入的行
                if current_count > 1:
                    table_pieces.append(
                        (
                            "\n".join(current_rows),
                            current_count,
                            False,
                        )
                    )

                # 只有表头、没有数据行的情况
                if not table_pieces:
                    table_pieces.append(
                        (header_text, 1, False)
                    )

        for content, row_count, partial_row in table_pieces:
            metadata = first.metadata.copy()

            metadata["element_type"] = "merged_table"
            metadata["row_count"] = row_count

            # 表示此知识块是否包含被拆开的行
            metadata["partial_row"] = partial_row

            result.append(
                KnowledgeChunk(
                    content=content,
                    source_file=first.source_file,
                    source_type=first.source_type,
                    title=first.title,
                    page_number=first.page_number,
                    section=first.section,
                    metadata=metadata,
                )
            )

        table_buffer.clear()

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
            flush_table_buffer()
            result.append(chunk)

            current_section = None
            current_subsection = None
            current_source = None
            continue

        # 表格行进入表格缓冲区
        if element_type == "table_row":
            flush_buffer()

            if table_buffer:
                first_table = table_buffer[0]

                if (
                    chunk.metadata.get("table_index")
                    != first_table.metadata.get("table_index")
                    or chunk.source_file != first_table.source_file
                    or chunk.source_type != first_table.source_type
                ):
                    flush_table_buffer()

            table_buffer.append(chunk)

            current_section = None
            current_subsection = None
            current_source = None
            continue

        # 其他特殊内容单独保留
        if element_type != "paragraph":
            flush_buffer()
            flush_table_buffer()
            result.append(chunk)

            current_section = None
            current_subsection = None
            current_source = None
            continue

        # 遇到普通正文，先保存之前的表格
        flush_table_buffer()

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
    flush_table_buffer()

    return result
