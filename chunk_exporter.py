import json

from knowledge_schema import KnowledgeChunk


def prepare_export(chunks: list[KnowledgeChunk]) -> list[dict]:
    """
    为最终知识块生成编号，并转换成可导出的字典列表。

    chunks: 已完成解析和分块的知识块列表
    """

    result = []

    for index, chunk in enumerate(chunks, start=1):

        data = chunk.to_dict()

        data["chunk_id"] = f"chunk_{index:04d}"

        result.append(data)

    return result
def chunks_to_json(chunks):
    """将知识块导出为 JSON 字符串。"""
    data = prepare_export(chunks)

    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )


def chunks_to_markdown(chunks):
    """将知识块导出为 Markdown 字符串。"""
    markdown_parts = []

    data_list = prepare_export(chunks)

    for data in data_list:
        metadata = data["metadata"]
        subsection = metadata.get("subsection")

        part = (
            f"## 知识块 {data['chunk_id']}\n\n"
            f"所属章节：{data['section'] or '未识别'}\n\n"
            f"所属标题：{subsection or '未识别'}\n\n"
            f"来源文件：{data['source_file']}\n\n"
            f"文件类型：{data['source_type']}\n\n"
            f"字符数：{metadata['char_count']}\n\n"
        )

        if data["page_number"] is not None:
            part += f"来源页码：{data['page_number']}\n\n"

        part += f"具体内容：\n\n{data['content']}\n"

        markdown_parts.append(part)

    return "\n\n---\n\n".join(markdown_parts)