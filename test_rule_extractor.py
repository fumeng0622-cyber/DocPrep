import unittest

from rule_extractor import extract_rules


class BodyFormatTests(unittest.TestCase):
    def test_single_natural_sentence_is_a_rule(self):
        sentence = "正文一般使用仿宋_GB2312，三号字。"
        records = extract_rules([sentence])

        self.assertEqual(len(records), 1)
        rule = records[0]
        self.assertEqual(rule["记录类型"], "规范条目")
        self.assertEqual(rule["规范名称"], "正文")
        self.assertEqual(rule["字体要求"], "仿宋_GB2312")
        self.assertEqual(rule["字号要求"], "三号")
        self.assertEqual(rule["原始内容"], [sentence])
        self.assertIsNone(rule["所属章节"])

    def test_normal_first_paragraph_remains_document_title(self):
        records = extract_rules(["公文格式要求"])

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["记录类型"], "文档标题")
        self.assertEqual(records[0]["规范名称"], "公文格式要求")
        self.assertIsNone(records[0]["字体要求"])
        self.assertIsNone(records[0]["字号要求"])

    def test_natural_sentence_is_one_complete_rule(self):
        sentence = "正文一般使用仿宋_GB2312，三号字。"
        records = extract_rules(["格式要求", "三、正文格式", sentence])

        self.assertEqual(len(records), 3)
        rule = records[-1]
        self.assertEqual(rule["记录类型"], "规范条目")
        self.assertEqual(rule["规范名称"], "正文")
        self.assertEqual(rule["所属章节"], "三、正文格式")
        self.assertEqual(rule["字体要求"], "仿宋_GB2312")
        self.assertEqual(rule["字号要求"], "三号")
        self.assertEqual(rule["原始内容"], [sentence])

    def test_explicit_labels_keep_existing_behavior(self):
        records = extract_rules([
            "格式要求", "（一）正文", "字体：仿宋_GB2312", "字号：三号"
        ])

        self.assertEqual(len(records), 2)
        self.assertEqual(records[-1]["字体要求"], "仿宋_GB2312")
        self.assertEqual(records[-1]["字号要求"], "三号")
        self.assertEqual(records[-1]["原始内容"], [
            "（一）正文", "字体：仿宋_GB2312", "字号：三号"
        ])

    def test_body_sentence_does_not_change_previous_title_rule(self):
        records = extract_rules([
            "格式要求", "（一）大标题", "字体：黑体",
            "正文一般使用仿宋_GB2312，三号字。"
        ])

        self.assertEqual(len(records), 3)
        self.assertEqual(records[1]["字体要求"], "黑体")
        self.assertIsNone(records[1]["字号要求"])
        self.assertEqual(records[2]["规范名称"], "正文")

    def test_unrelated_sentence_is_still_pending(self):
        sentence = "正文应当表述准确。"
        records = extract_rules(["格式要求", sentence])

        self.assertEqual(records[-1]["记录类型"], "待确认内容")
        self.assertEqual(records[-1]["原始内容"], [sentence])


if __name__ == "__main__":
    unittest.main()
