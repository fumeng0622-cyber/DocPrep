
import unittest

from knowledge_schema import KnowledgeChunk
from knowledge_processor import attach_section_context
from chunk_builder import build_chunks, split_long_text


def make_chunk(content, element_type="paragraph"):
    """创建用于测试的知识片段。"""
    return KnowledgeChunk(
        content=content,
        source_file="测试.docx",
        source_type="docx",
        metadata={"element_type": element_type},
    )


class ChunkBuilderTests(unittest.TestCase):

    def test_merge_paragraphs_in_same_section(self):
        """同一章节下的相邻正文应该合并。"""
        chunks = [
            make_chunk("第一章 Python 基础"),
            make_chunk("Python 是一种编程语言。"),
            make_chunk("Python 具有简洁易读的特点。"),
        ]

        processed = attach_section_context(chunks)
        result = build_chunks(processed)

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[1].content,
            "Python 是一种编程语言。\nPython 具有简洁易读的特点。"
        )

    def test_different_subsections_are_not_merged(self):
        """不同二级标题下的正文不能合并。"""
        chunks = [
            make_chunk("第一章 Python 基础"),
            make_chunk("1.1 变量"),
            make_chunk("变量用于存储数据。"),
            make_chunk("1.2 数据类型"),
            make_chunk("Python 支持整数类型。"),
        ]

        processed = attach_section_context(chunks)
        result = build_chunks(processed)

        self.assertEqual(len(result), 5)
        self.assertEqual(
            result[2].metadata["subsection"],
            "1.1 变量"
        )
        self.assertEqual(
            result[4].metadata["subsection"],
            "1.2 数据类型"
        )

    def test_max_chars_limits_merging(self):
        """合并后超过最大长度时，应该拆成多个知识块。"""
        chunks = [
            make_chunk("第一章 Python 基础"),
            make_chunk("A" * 10),
            make_chunk("B" * 10),
        ]

        processed = attach_section_context(chunks)

        result = build_chunks(
            processed,
            max_chars=15,
            overlap=0
        )

        self.assertEqual(len(result), 3)
        self.assertEqual(result[1].content, "A" * 10)
        self.assertEqual(result[2].content, "B" * 10)

    def test_table_rows_are_kept_separate(self):
        """表格内容暂时不与普通正文合并。"""
        chunks = [
            make_chunk("一、总体要求"),
            make_chunk("正文第一段"),
            make_chunk("表格中的数据", "table_row"),
            make_chunk("正文第二段"),
        ]

        processed = attach_section_context(chunks)
        result = build_chunks(processed)

        self.assertEqual(len(result), 4)
        self.assertEqual(
            result[2].metadata["element_type"],
            "table_row"
        )

    def test_empty_input(self):
        """没有输入内容时，应该返回空列表。"""
        result = build_chunks([])

        self.assertEqual(result, [])

    def test_long_text_is_split(self):
        """超长文本拆分后，每块都不能超过长度限制。"""
        text = "Python是一种编程语言。" * 150

        result = split_long_text(
            text,
            max_chars=800,
            overlap=100
        )

        self.assertGreater(len(result), 1)

        for piece in result:
            self.assertLessEqual(len(piece), 800)

    def test_overlap_preserves_context(self):
        """超长单句拆分时，仍保留字符级重叠。"""
        text = "A" * 1500

        result = split_long_text(
            text,
            max_chars=800,
            overlap=100
        )

        self.assertGreater(len(result), 1)

        for piece in result:
            self.assertLessEqual(len(piece), 800)

        self.assertEqual(
            result[0][-100:],
            result[1][:100]
        )

    # ---------- 新增测试 1 ----------

    def test_overlap_prefers_complete_sentences(self):
        """普通长文本的重叠部分应尽量保留完整句子。"""

        sentence = "这是一个完整的测试句子。"
        text = sentence * 20

        result = split_long_text(
            text,
            max_chars=100,
            overlap=30
        )

        self.assertGreater(len(result), 1)

        for piece in result:
            self.assertLessEqual(len(piece), 100)
            self.assertTrue(piece.startswith("这是"))

        # 第二块应从完整句子开始
        self.assertTrue(result[1].startswith(sentence))

        # 相邻块确实保留了重叠句子
        self.assertTrue(
            result[0].endswith(sentence)
        )

    # ---------- 新增测试 2 ----------

    def test_very_long_sentence_split(self):
        """单个句子超过长度限制时，应正确拆分。"""

        text = "A" * 250

        result = split_long_text(
            text,
            max_chars=100,
            overlap=20
        )

        self.assertGreater(len(result), 1)

        for piece in result:
            self.assertLessEqual(len(piece), 100)

        for index in range(len(result) - 1):
            self.assertEqual(
                result[index][-20:],
                result[index + 1][:20]
            )

    # ---------- 新增测试 3 ----------

    def test_split_preserves_original_content(self):
        """移除相邻块的重叠部分后，应能还原原文。"""

        sentence = "Python支持知识库文档处理。"
        text = sentence * 30

        result = split_long_text(
            text,
            max_chars=100,
            overlap=30
        )

        restored = result[0]

        for piece in result[1:]:
            # 找到上一块末尾与当前块开头的最长匹配
            max_overlap = min(
                len(restored),
                len(piece),
                30
            )

            matched = 0

            for length in range(max_overlap, 0, -1):
                if restored[-length:] == piece[:length]:
                    matched = length
                    break

            restored += piece[matched:]

        self.assertEqual(restored, text)


if __name__ == "__main__":
    unittest.main()
