
from knowledge_schema import KnowledgeChunk


def decode_text(file_bytes):
    """
    将文件的二进制内容转换成字符串。
    支持常见的 UTF-8 和 GB18030 编码。
    """

    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError("无法识别文本文件的编码")


def parse_txt(file_bytes, filename):
    """
    解析 TXT 文件，生成 KnowledgeChunk 列表。

    file_bytes: 文件二进制内容
    filename: 原始文件名
    """

    text = decode_text(file_bytes)

    # 统一换行符
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 去除文件首尾空白
    text = text.strip()

    if not text:
        return []

    chunk = KnowledgeChunk(
        content=text,
        source_file=filename,
        source_type="txt",
        title=filename,
        page_number=None,
        section=None,
        metadata={
            "element_type": "paragraph",
            "encoding_normalized": True,
            "char_count": len(text)
        }
    )

    return [chunk]

import re


def parse_markdown(file_bytes, filename):
    """
    解析 Markdown 文件，识别标题和正文，
    并生成 KnowledgeChunk 列表。
    """

    text = decode_text(file_bytes)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if not text.strip():
        return []

    chunks = []
    current_section = None
    current_subsection = None
    buffer = []
    in_code_block = False

    def flush_buffer():
        """将暂存的正文保存为知识块。"""

        if not buffer:
            return

        content = "\n".join(buffer).strip()

        if content:
            chunks.append(
                KnowledgeChunk(
                    content=content,
                    source_file=filename,
                    source_type="md",
                    title=filename,
                    page_number=None,
                    section=current_section,
                    metadata={
                        "element_type": "paragraph",
                        "subsection": current_subsection,
                    }
                )
            )

        buffer.clear()

    for line in text.split("\n"):

        # 代码块内的 # 不应该被识别为标题
        if re.match(r"^\s*(```|~~~)", line):
            in_code_block = not in_code_block
            buffer.append(line)
            continue

        if not in_code_block:
            match = re.match(
                r"^(#{1,6})\s+(.+?)\s*$",
                line
            )

            if match:
                flush_buffer()

                level = len(match.group(1))
                heading_text = match.group(2)

                if level == 1:
                    current_section = heading_text
                    current_subsection = None

                elif level == 2:
                    current_subsection = heading_text

                chunks.append(
                    KnowledgeChunk(
                        content=heading_text,
                        source_file=filename,
                        source_type="md",
                        title=filename,
                        page_number=None,
                        section=current_section,
                        metadata={
                            "element_type": "heading",
                            "heading_level": level,
                            "subsection": current_subsection,
                        }
                    )
                )

                continue

        buffer.append(line)

    flush_buffer()

    return chunks

