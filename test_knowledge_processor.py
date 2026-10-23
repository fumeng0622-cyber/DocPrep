
import unittest

from knowledge_schema import KnowledgeChunk
from knowledge_processor import attach_section_context


def make_chunk(content, element_type="paragraph"):
    """创建一条测试用的知识片段。"""
    return KnowledgeChunk(
        content=content,
        source_file="测试.docx",
        source_type="docx",
        metadata={"element_type": element_type},
    )


class KnowledgeProcessorTests(unittest.TestCase):

    def test_section_is_attached_to_body(self):
        """正文应该继承前面的章节标题。"""
        chunks = [
            make_chunk("一、总体要求"),
            make_chunk("公文应当格式规范。"),
        ]

        result = attach_section_context(chunks)

        self.assertEqual(
            result[1].section,
            "一、总体要求"
        )

    def test_section_changes_when_new_heading_appears(self):
        """遇到新章节时，所属章节应该更新。"""
        chunks = [
            make_chunk("一、总体要求"),
            make_chunk("第一章的内容"),
            make_chunk("二、标题格式"),
            make_chunk("第二章的内容"),
        ]

        result = attach_section_context(chunks)

        self.assertEqual(
            result[1].section,
            "一、总体要求"
        )
        self.assertEqual(
            result[3].section,
            "二、标题格式"
        )

    def test_content_before_section_has_no_section(self):
        """章节标题之前的内容不应被错误归类。"""
        chunks = [
            make_chunk("公文规范测试样例"),
            make_chunk("一、总体要求"),
        ]

        result = attach_section_context(chunks)

        self.assertIsNone(result[0].section)

    def test_table_content_is_not_treated_as_heading(self):
        """表格中的章节样式文字不能改变当前章节。"""
        chunks = [
            make_chunk("一、总体要求"),
            make_chunk("二、表格内容", "table_row"),
            make_chunk("后续正文"),
        ]

        result = attach_section_context(chunks)

        self.assertEqual(
            result[2].section,
            "一、总体要求"
        )

    def test_original_chunks_are_not_modified(self):
        """处理章节时，不应该修改原始知识片段。"""
        chunks = [
            make_chunk("一、总体要求"),
            make_chunk("正文内容"),
        ]

        result = attach_section_context(chunks)

        self.assertIsNone(chunks[1].section)
        self.assertEqual(
            result[1].section,
            "一、总体要求"
        )

    def test_subsection_is_attached_to_body(self):
        """正文应该继承前面的一级章节和二级标题。"""
        chunks = [
            make_chunk("二、标题格式"),
            make_chunk("（一）公文大标题"),
            make_chunk("字体：长城小标宋简体"),
        ]

        result = attach_section_context(chunks)

        self.assertEqual(
            result[2].section,
            "二、标题格式"
        )
        self.assertEqual(
            result[2].metadata["subsection"],
            "（一）公文大标题"
        )

    def test_new_section_clears_subsection(self):
        """进入新的一级章节后，旧的二级标题应当清空。"""
        chunks = [
            make_chunk("二、标题格式"),
            make_chunk("（一）公文大标题"),
            make_chunk("三、正文格式"),
            make_chunk("正文一般使用仿宋字体。"),
        ]

        result = attach_section_context(chunks)

        self.assertEqual(
            result[3].section,
            "三、正文格式"
        )
        self.assertIsNone(
            result[3].metadata["subsection"]
        )

    # 以下是新增的通用章节识别测试

    def test_chapter_heading_is_recognized(self):
        """识别第一章形式的章节标题。"""
        chunks = [
            make_chunk("第一章 Python 基础"),
            make_chunk("Python 是一种编程语言。"),
        ]

        result = attach_section_context(chunks)

        self.assertEqual(
            result[1].section,
            "第一章 Python 基础"
        )

    def test_normal_sentence_is_not_chapter_heading(self):
        """普通正文不能被误认为章节标题。"""
        chunks = [
            make_chunk("一、总体要求"),
            make_chunk("第一章的内容"),
        ]

        result = attach_section_context(chunks)

        self.assertEqual(
            result[1].section,
            "一、总体要求"
        )

    def test_numbered_subsection_is_recognized(self):
        """识别 1.1 形式的二级标题。"""
        chunks = [
            make_chunk("第一章 Python 基础"),
            make_chunk("1.1 变量"),
            make_chunk("变量用于存储数据。"),
        ]

        result = attach_section_context(chunks)

        self.assertEqual(
            result[2].section,
            "第一章 Python 基础"
        )
        self.assertEqual(
            result[2].metadata["subsection"],
            "1.1 变量"
        )
    
    def test_document_title_detection(self):
        """验证 Word 主标题识别和标题信息继承。"""

        title_chunk = KnowledgeChunk(
            content="DocPrep 长文档分块验收测试",
            source_file="test.docx",
            source_type="docx",
            title=None,
            page_number=None,
            section=None,
            metadata={
                "element_type": "paragraph",
                "paragraph_style": "Title",
            },
        )

        body_chunk = KnowledgeChunk(
            content="这是一段测试说明。",
            source_file="test.docx",
            source_type="docx",
            title=None,
            page_number=None,
            section=None,
            metadata={
                "element_type": "paragraph",
                "paragraph_style": "Normal",
            },
        )

        result = attach_section_context(
            [title_chunk, body_chunk]
        )

        self.assertEqual(
            result[0].metadata["heading_level"], 0
        )

        self.assertEqual(
            result[0].title,
            "DocPrep 长文档分块验收测试"
        )

        self.assertEqual(
            result[1].title,
            "DocPrep 长文档分块验收测试"
        )

        self.assertIsNone(
            result[1].metadata["heading_level"]
        )



if __name__ == "__main__":
    unittest.main()
