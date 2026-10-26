import json
import unittest

from knowledge_schema import KnowledgeChunk
from chunk_exporter import chunks_to_json, chunks_to_markdown


class ExportTests(unittest.TestCase):

    def setUp(self):
        self.chunks = [
            KnowledgeChunk(
                content="Python 是一种编程语言。",
                source_file="测试.docx",
                source_type="docx",
                section="一、Python 简介",
                metadata={"subsection": "（一）基础概念"}
            ),
            KnowledgeChunk(
                content="def add(a, b):\n    return a + b",
                source_file="测试.docx",
                source_type="docx",
                page_number=2
            )
        ]

    def test_json_ids(self):
        data = json.loads(chunks_to_json(self.chunks))

        self.assertEqual(data[0]["chunk_id"], "chunk_0001")
        self.assertEqual(data[1]["chunk_id"], "chunk_0002")

    def test_json_chinese(self):
        data = json.loads(chunks_to_json(self.chunks))

        self.assertEqual(
            data[0]["content"],
            "Python 是一种编程语言。"
        )

    def test_markdown_ids(self):
        result = chunks_to_markdown(self.chunks)

        self.assertIn("chunk_0001", result)
        self.assertIn("chunk_0002", result)

    def test_markdown_section(self):
        result = chunks_to_markdown(self.chunks)

        self.assertIn("一、Python 简介", result)
        self.assertIn("（一）基础概念", result)

    def test_markdown_page_number(self):
        result = chunks_to_markdown(self.chunks)

        self.assertIn("来源页码：2", result)

    def test_markdown_code(self):
        result = chunks_to_markdown(self.chunks)

        self.assertIn("def add(a, b):", result)
        self.assertIn("return a + b", result)


if __name__ == "__main__":
    unittest.main()