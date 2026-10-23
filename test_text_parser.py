
import unittest

from text_parser import decode_text, parse_txt


class TextParserTests(unittest.TestCase):

    def test_basic_txt_parsing(self):
        """测试普通中文 TXT 文件。"""

        text = "人工智能基础\n机器学习是人工智能的重要分支。"

        result = parse_txt(
            text.encode("utf-8"),
            "人工智能.txt"
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].content, text)

    def test_empty_file(self):
        """测试空文件。"""

        result = parse_txt(b"", "空文件.txt")

        self.assertEqual(result, [])

    def test_whitespace_only_file(self):
        """测试只有空白字符的文件。"""

        result = parse_txt(
            " \n\t ".encode("utf-8"),
            "空白文件.txt"
        )

        self.assertEqual(result, [])

    def test_utf8_bom(self):
        """测试带 BOM 的 UTF-8 文件。"""

        text = "这是一个中文测试文件。"

        result = parse_txt(
            text.encode("utf-8-sig"),
            "BOM测试.txt"
        )

        self.assertEqual(result[0].content, text)

    def test_gb18030_encoding(self):
        """测试 Windows 常见中文编码。"""

        text = "中文文档解析测试"

        result = parse_txt(
            text.encode("gb18030"),
            "中文编码.txt"
        )

        self.assertEqual(result[0].content, text)

    def test_newline_and_metadata(self):
        """测试换行符标准化及来源信息。"""

        result = parse_txt(
            b"First line\r\nSecond line\rThird line",
            "notes.txt"
        )

        self.assertEqual(
            result[0].content,
            "First line\nSecond line\nThird line"
        )

        chunk = result[0]

        self.assertEqual(chunk.source_file, "notes.txt")
        self.assertEqual(chunk.source_type, "txt")
        self.assertEqual(chunk.title, "notes.txt")
        self.assertIsNone(chunk.page_number)
        self.assertIsNone(chunk.section)

        self.assertEqual(
            chunk.metadata["element_type"],
            "paragraph"
        )

        self.assertEqual(
            chunk.metadata["char_count"],
            len(chunk.content)
        )


if __name__ == "__main__":
    unittest.main()
