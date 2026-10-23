
import pymupdf

from knowledge_schema import KnowledgeChunk


def parse_pdf(file_bytes, filename):
    """
    解析 PDF 文件，按页提取文字并生成知识块。

    file_bytes: PDF 文件的二进制内容
    filename: 原始文件名

    返回：KnowledgeChunk 列表
    """

    chunks = []

    # 从内存中的二进制数据打开 PDF
    document = pymupdf.open(
        stream=file_bytes,
        filetype="pdf"
    )

    try:
        # 逐页读取 PDF
        for page_index, page in enumerate(document):

            # 页码从 1 开始
            page_number = page_index + 1

            # 提取当前页面的文字
            text = page.get_text("text").strip()

            # 跳过没有可提取文字的页面
            if not text:
                continue

            # 创建知识块
            chunk = KnowledgeChunk(
                content=text,
                source_file=filename,
                source_type="pdf",
                title=filename,
                page_number=page_number,
                section=None,
                metadata={
                    "element_type": "pdf_page",
                    "page_number": page_number,
                    "char_count": len(text)
                }
            )

            chunks.append(chunk)

    finally:
        document.close()

    return chunks
