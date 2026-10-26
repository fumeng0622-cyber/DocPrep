import unittest

from knowledge_schema import KnowledgeChunk
from chunk_exporter import prepare_export


class ChunkExporterTests(unittest.TestCase):

    def test_chunk_ids_are_sequential(self):
        """测试知识块编号是否连续。"""

        chunks = [
            KnowledgeChunk(
                content="第一段内容",
                source_file="测试.docx",
                source_type="docx"
            ),
            KnowledgeChunk(
                content="第二段内容",
                source_file="测试.docx",
                source_type="docx"
            ),
        ]

        result = prepare_export(chunks)

        self.assertEqual(result[0]["chunk_id"], "chunk_0001")
        self.assertEqual(result[1]["chunk_id"], "chunk_0002")

    def test_original_chunks_are_unchanged(self):
        """测试导出操作不会修改原始知识块。"""

        chunk = KnowledgeChunk(
            content="Python基础",
            source_file="测试.docx",
            source_type="docx"
        )

        result = prepare_export([chunk])

        self.assertEqual(chunk.metadata, {})
        self.assertEqual(result[0]["metadata"]["char_count"], len(chunk.content))


if __name__ == "__main__":
    unittest.main()