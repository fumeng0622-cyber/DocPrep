
import unittest

from text_parser import parse_markdown


class MarkdownParserTests(unittest.TestCase):

    def parse(self, text):
        """将测试字符串转换成 Markdown 知识块。"""
        return parse_markdown(
            text.encode("utf-8"),
            "test.md"
        )

    def test_basic_heading(self):
        """测试一级标题识别。"""
        chunks = self.parse("# Python 基础\n\nPython 是编程语言。")

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].content, "Python 基础")
        self.assertEqual(chunks[0].metadata["heading_level"], 1)
        self.assertEqual(chunks[1].section, "Python 基础")

    def test_second_level_heading(self):
        """测试二级标题及章节归属。"""
        chunks = self.parse(
            "# 人工智能\n## 机器学习\n监督学习是一种方法。"
        )

        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[1].metadata["heading_level"], 2)
        self.assertEqual(chunks[2].section, "人工智能")
        self.assertEqual(
            chunks[2].metadata["subsection"],
            "机器学习"
        )

    def test_six_heading_levels(self):
        """测试 Markdown 六级标题。"""
        text = "\n".join(
            "#" * level + f" 标题{level}"
            for level in range(1, 7)
        )

        chunks = self.parse(text)

        self.assertEqual(len(chunks), 6)
        self.assertEqual(
            [c.metadata["heading_level"] for c in chunks],
            [1, 2, 3, 4, 5, 6]
        )

    def test_code_block_protection(self):
        """测试代码块中的 # 不被当作标题。"""
        chunks = self.parse(
            "# 示例\n"
            "```python\n"
            "# 这是 Python 注释\n"
            "print('hello')\n"
            "```\n"
        )

        self.assertEqual(len(chunks), 2)
        self.assertEqual(
            chunks[1].metadata["element_type"],
            "paragraph"
        )
        self.assertIn(
            "# 这是 Python 注释",
            chunks[1].content
        )

    def test_empty_markdown(self):
        """测试空 Markdown 文件。"""
        self.assertEqual(self.parse(""), [])

    def test_plain_text_markdown(self):
        """测试没有标题的 Markdown 文件。"""
        chunks = self.parse("这是普通正文。\n第二行内容。")

        self.assertEqual(len(chunks), 1)
        self.assertIsNone(chunks[0].section)
        self.assertIn("第二行内容", chunks[0].content)

    def test_heading_switch(self):
        """测试切换一级标题时清除旧二级标题。"""
        chunks = self.parse(
            "# 第一章\n"
            "## 第一节\n"
            "第一章内容\n"
            "# 第二章\n"
            "第二章内容"
        )

        last_chunk = chunks[-1]

        self.assertEqual(last_chunk.section, "第二章")
        self.assertIsNone(
            last_chunk.metadata["subsection"]
        )

    def test_metadata(self):
        """测试来源文件和知识块元数据。"""
        chunks = self.parse("# 标题\n正文内容")

        self.assertEqual(chunks[0].source_file, "test.md")
        self.assertEqual(chunks[0].source_type, "md")
        self.assertEqual(chunks[0].title, "test.md")
        self.assertIsNone(chunks[0].page_number)
        self.assertEqual(
            chunks[1].metadata["element_type"],
            "paragraph"
        )


if __name__ == "__main__":
    unittest.main()
