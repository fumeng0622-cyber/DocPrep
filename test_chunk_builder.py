
import unittest

from knowledge_schema import KnowledgeChunk
from knowledge_processor import attach_section_context
from chunk_builder import build_chunks, split_long_text


def make_chunk(content, element_type="paragraph", table_index=None):
    """创建用于测试的知识片段。"""

    metadata = {"element_type": element_type}

    if table_index is not None:
        metadata["table_index"] = table_index

    return KnowledgeChunk(
        content=content,
        source_file="测试.docx",
        source_type="docx",
        metadata=metadata,
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
        """表格内容不与普通正文合并。"""

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
            "merged_table"
        )

        self.assertEqual(
        result[2].content,
        "表格中的数据"
        )
    def test_table_rows_are_merged(self):
        """同一张表格的连续行应该合并。"""

        chunks = [
            make_chunk("编号 | 主题", "table_row", 1),
            make_chunk("P01 | 变量", "table_row", 1),
            make_chunk("P02 | 循环", "table_row", 1),
        ]

        result = build_chunks(chunks)

        self.assertEqual(len(result), 1)

        self.assertEqual(
            result[0].content,
            "编号 | 主题\nP01 | 变量\nP02 | 循环"
        )

        self.assertEqual(
            result[0].metadata["element_type"],
            "merged_table"
        )

        self.assertEqual(
            result[0].metadata["row_count"],
            3
        )

        self.assertEqual(
            result[0].metadata["table_index"],
            1
        )

    def test_table_rows_are_merged(self):
        """同一张表格的连续行应该合并。"""

        chunks = [
            make_chunk("编号 | 主题", "table_row", 1),
            make_chunk("P01 | 变量", "table_row", 1),
            make_chunk("P02 | 循环", "table_row", 1),
        ]

        result = build_chunks(chunks)

        self.assertEqual(len(result), 1)

        self.assertEqual(
            result[0].content,
            "编号 | 主题\nP01 | 变量\nP02 | 循环"
        )

        self.assertEqual(
            result[0].metadata["element_type"],
            "merged_table"
        )

        self.assertEqual(
            result[0].metadata["row_count"],
            3
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

    def test_different_tables_are_not_merged(self):
        """不同表格的行不能合并。"""

        chunks = [
            make_chunk("编号 | 课程", "table_row", 1),
            make_chunk("01 | Python", "table_row", 1),
            make_chunk("编号 | 考试方式", "table_row", 2),
            make_chunk("01 | 闭卷", "table_row", 2),
        ]

        result = build_chunks(chunks)

        self.assertEqual(len(result), 2)

        self.assertEqual(
            result[0].metadata["table_index"],
            1
        )

        self.assertEqual(
            result[1].metadata["table_index"],
            2
        )

        self.assertEqual(
            result[0].metadata["row_count"],
            2
        )

        self.assertEqual(
            result[1].metadata["row_count"],
            2
        )
    def test_long_table_is_split(self):
        """超长表格应该按完整行拆分，并保留表头。"""

        chunks = [
            make_chunk("编号 | 内容", "table_row", 1),
            make_chunk("01 | Python基础", "table_row", 1),
            make_chunk("02 | 数据类型", "table_row", 1),
            make_chunk("03 | 循环结构", "table_row", 1),
        ]

        result = build_chunks(
            chunks,
            max_chars=30,
            overlap=0
        )

        self.assertGreater(len(result), 1)

        for chunk in result:
            self.assertLessEqual(len(chunk.content), 30)
            self.assertTrue(
                chunk.content.startswith("编号 | 内容")
            )

    def test_very_long_table_header(self):
        """表头超长时，拆分后应能还原原始内容。"""

        header = "字段名称" * 30
        data_row = "01 | Python基础"

        chunks = [
            make_chunk(header, "table_row", 1),
            make_chunk(data_row, "table_row", 1),
        ]

        result = build_chunks(
            chunks,
            max_chars=50,
            overlap=0
        )

        self.assertGreater(len(result), 1)

        for chunk in result:
            self.assertLessEqual(len(chunk.content), 50)
            self.assertTrue(
                chunk.metadata["partial_row"]
            )

        restored = "".join(
            chunk.content for chunk in result
        )

        self.assertEqual(
            restored,
            header + "\n" + data_row
        )
    def test_very_long_table_row(self):
        """单行超长时，拆分后应能还原原始内容。"""

        header = "编号 | 内容"
        long_row = "01 | " + "Python知识点" * 30

        chunks = [
            make_chunk(header, "table_row", 1),
            make_chunk(long_row, "table_row", 1),
        ]

        result = build_chunks(
            chunks,
            max_chars=100,
            overlap=0
        )

        self.assertGreater(len(result), 1)

        restored = ""

        for chunk in result:
            self.assertLessEqual(len(chunk.content), 100)

            self.assertTrue(
                chunk.content.startswith(header + "\n")
            )

            self.assertTrue(
                chunk.metadata["partial_row"]
            )

            restored += chunk.content[len(header) + 1:]

        self.assertEqual(restored, long_row)
    def test_long_table_preserves_all_rows(self):
        """超长表格拆分后，所有数据行都应完整保留。"""

        rows = [
            "编号 | 内容",
            "01 | Python基础",
            "02 | 数据类型",
            "03 | 循环结构",
            "04 | 函数定义",
        ]

        chunks = [
            make_chunk(row, "table_row", 1)
            for row in rows
        ]

        result = build_chunks(
            chunks,
            max_chars=30,
            overlap=0
        )

        # 所有知识块都不能超长
        for chunk in result:
            self.assertLessEqual(len(chunk.content), 30)

        # 每个知识块都应该包含表头
        for chunk in result:
            self.assertTrue(
                chunk.content.startswith(rows[0])
            )

        # 去除重复表头，还原所有数据行
        restored_rows = []

        for chunk in result:
            lines = chunk.content.split("\n")
            restored_rows.extend(lines[1:])

        self.assertEqual(restored_rows, rows[1:])
    
    def test_paragraph_table_order(self):
        """正文和表格应该保持原来的顺序。"""

        chunks = [
            make_chunk("第一段正文"),
            make_chunk("编号 | 课程", "table_row", 1),
            make_chunk("01 | Python", "table_row", 1),
            make_chunk("第二段正文"),
        ]

        result = build_chunks(chunks)

        self.assertEqual(len(result), 3)

        self.assertEqual(
            result[0].content,
            "第一段正文"
        )

        self.assertEqual(
            result[1].content,
            "编号 | 课程\n01 | Python"
        )

        self.assertEqual(
            result[2].content,
            "第二段正文"
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
