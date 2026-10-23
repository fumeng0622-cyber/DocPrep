
import unittest

import pymupdf

from pdf_parser import parse_pdf


def create_pdf_bytes(page_texts):
    """
    在内存中创建测试 PDF。

    page_texts: 每页的文字内容列表。
    例如：["第一页", "", "第三页"]
    """

    document = pymupdf.open()

    try:
        for text in page_texts:
            page = document.new_page()

            if text:
                page.insert_text(
                    (72, 72),
                    text,
                    fontsize=12
                )

        return document.tobytes()

    finally:
        document.close()


class PDFParserTests(unittest.TestCase):

    def test_single_page(self):
        """测试单页 PDF。"""

        file_bytes = create_pdf_bytes([
            "Hello PDF"
        ])

        result = parse_pdf(
            file_bytes,
            "test.pdf"
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0].content,
            "Hello PDF"
        )

    def test_multiple_pages(self):
        """测试多页 PDF。"""

        file_bytes = create_pdf_bytes([
            "First page",
            "Second page",
            "Third page"
        ])

        result = parse_pdf(
            file_bytes,
            "multiple.pdf"
        )

        self.assertEqual(len(result), 3)

        self.assertEqual(
            [chunk.page_number for chunk in result],
            [1, 2, 3]
        )

    def test_empty_page_is_skipped(self):
        """测试空白页是否跳过。"""

        file_bytes = create_pdf_bytes([
            "First page",
            "",
            "Third page"
        ])

        result = parse_pdf(
            file_bytes,
            "empty_page.pdf"
        )

        self.assertEqual(len(result), 2)

        self.assertEqual(
            [chunk.page_number for chunk in result],
            [1, 3]
        )

    def test_metadata(self):
        """测试 PDF 来源信息。"""

        file_bytes = create_pdf_bytes([
            "PDF content"
        ])

        result = parse_pdf(
            file_bytes,
            "document.pdf"
        )

        chunk = result[0]

        self.assertEqual(
            chunk.source_file,
            "document.pdf"
        )

        self.assertEqual(
            chunk.source_type,
            "pdf"
        )

        self.assertEqual(
            chunk.title,
            "document.pdf"
        )

        self.assertEqual(
            chunk.metadata["element_type"],
            "pdf_page"
        )

        self.assertEqual(
            chunk.metadata["page_number"],
            1
        )

        self.assertEqual(
            chunk.metadata["char_count"],
            len(chunk.content)
        )

    def test_all_empty_pages(self):
        """测试全部为空白页的 PDF。"""

        file_bytes = create_pdf_bytes([
            "",
            ""
        ])

        result = parse_pdf(
            file_bytes,
            "blank.pdf"
        )

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
