
import unittest

from knowledge_schema import KnowledgeChunk, validate_chunk


class KnowledgeChunkTests(unittest.TestCase):

    def test_valid_chunk(self):
        chunk = KnowledgeChunk(
            content="公文大标题格式要求",
            source_file="规范.docx",
            source_type="docx",
            title="大标题",
            page_number=1,
        )

        validate_chunk(chunk)

        self.assertEqual(chunk.content, "公文大标题格式要求")
        self.assertEqual(chunk.source_file, "规范.docx")
        self.assertEqual(chunk.page_number, 1)

    def test_empty_content_is_rejected(self):
        chunk = KnowledgeChunk(
            content="   ",
            source_file="规范.docx",
            source_type="docx",
        )

        with self.assertRaises(ValueError):
            validate_chunk(chunk)

    def test_empty_source_file_is_rejected(self):
        chunk = KnowledgeChunk(
            content="测试内容",
            source_file=" ",
            source_type="docx",
        )

        with self.assertRaises(ValueError):
            validate_chunk(chunk)

    def test_invalid_page_number_is_rejected(self):
        chunk = KnowledgeChunk(
            content="测试内容",
            source_file="规范.pdf",
            source_type="pdf",
            page_number=0,
        )

        with self.assertRaises(ValueError):
            validate_chunk(chunk)

    def test_chunk_can_be_converted_to_dict(self):
        chunk = KnowledgeChunk(
            content="测试内容",
            source_file="规范.docx",
            source_type="docx",
        )

        result = chunk.to_dict()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["content"], "测试内容")
        self.assertIn("metadata", result)


if __name__ == "__main__":
    unittest.main()
