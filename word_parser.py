
from io import BytesIO

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from knowledge_schema import KnowledgeChunk, validate_chunk


def parse_docx(file_bytes: bytes, source_file: str) -> list[KnowledgeChunk]:
    """
    解析 Word 文档，将正文段落和表格转换成统一的知识片段。

    file_bytes: Word 文件的二进制内容。
    source_file: 原始文件名。

    返回：KnowledgeChunk 对象列表。
    """

    document = Document(BytesIO(file_bytes))
    chunks = []

    paragraph_index = 0
    table_index = 0

    # 按照文档中的实际顺序遍历段落和表格
    for element in document.element.body.iterchildren():

        # 处理普通段落
        if element.tag.endswith("}p"):
            paragraph = Paragraph(element, document)
            content = paragraph.text.strip()

            if not content:
                continue

            paragraph_index += 1

            chunk = KnowledgeChunk(
                content=content,
                source_file=source_file,
                source_type="docx",
                section=paragraph.style.name,
                metadata={
                    "element_type": "paragraph",
                    "paragraph_index": paragraph_index,
                    "paragraph_style": paragraph.style.name,
                },
            )

            validate_chunk(chunk)
            chunks.append(chunk)

        # 处理表格
        elif element.tag.endswith("}tbl"):
            table = Table(element, document)
            table_index += 1

            for row_index, row in enumerate(table.rows, start=1):
                cell_values = [
                    cell.text.strip().replace("\n", "；")
                    for cell in row.cells
                ]

                # 跳过完全为空的行
                if not any(cell_values):
                    continue

                content = " | ".join(cell_values)

                chunk = KnowledgeChunk(
                    content=content,
                    source_file=source_file,
                    source_type="docx",
                    metadata={
                        "element_type": "table_row",
                        "table_index": table_index,
                        "row_index": row_index,
                        "cell_count": len(cell_values),
                    },
                )

                validate_chunk(chunk)
                chunks.append(chunk)

    return chunks
