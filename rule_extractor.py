
import re


def extract_rules(paragraph_texts):
    """
    识别公文中的文档标题、章节标题、具体规范和待确认内容。

    paragraph_texts：Word 非空段落组成的字符串列表。
    返回：结构化记录列表。
    """

    records = []
    current_section = None
    current_rule = None

    # 例如：一、总体要求 / 二、标题格式
    section_pattern = re.compile(
        r"^[一二三四五六七八九十百]+、\s*(.+)$"
    )

    # 例如：（一）公文大标题 / (二) 正文标题
    topic_pattern = re.compile(
        r"^[（(]\s*([一二三四五六七八九十百\d]+)\s*[）)]\s*(.+)$"
    )

    # 识别明确写出的格式要求
    field_patterns = {
        "字体要求": re.compile(r"^字体\s*[:：]\s*(.+)$"),
        "字号要求": re.compile(r"^字号\s*[:：]\s*(.+)$"),
        "字形要求": re.compile(r"^(?:字形|字体样式)\s*[:：]\s*(.+)$"),
        "颜色要求": re.compile(r"^字体颜色\s*[:：]\s*(.+)$"),
    }

    # 小范围支持：正文一般使用仿宋_GB2312，三号字。
    body_format_pattern = re.compile(
        r"^正文一般使用\s*([^，,\s]+)\s*[，,]\s*"
        r"([一二三四五六七八九十]+号)字[。.]?$"
    )

    def make_record(record_type, name, text):
        """创建统一格式的记录，方便后续网页展示和导出。"""
        return {
            "记录类型": record_type,
            "规范名称": name,
            "所属章节": current_section,
            "字体要求": None,
            "字号要求": None,
            "字形要求": None,
            "颜色要求": None,
            "原始内容": [text],
            "补充说明": [],
            "待确认": [],
        }

    for index, paragraph in enumerate(paragraph_texts):
        text = paragraph.strip()

        if not text:
            continue

        # 明确的自然语言格式要求优先识别，避免首段被误当作文档标题。
        body_match = body_format_pattern.match(text)

        if body_match:
            current_rule = make_record("规范条目", "正文", text)
            current_rule["字体要求"] = body_match.group(1)
            current_rule["字号要求"] = body_match.group(2)
            records.append(current_rule)
            continue

        # 未匹配上述格式要求的第一段作为文档标题保留
        if index == 0:
            record = make_record("文档标题", text, text)
            records.append(record)
            current_rule = None
            continue

        # 识别章节标题，例如“一、总体要求”
        section_match = section_pattern.match(text)

        if section_match:
            current_section = text
            current_rule = None

            records.append(
                make_record("章节标题", text, text)
            )
            continue

        # 识别具体规范标题，例如“（一）公文大标题”
        topic_match = topic_pattern.match(text)

        if topic_match:
            topic_name = topic_match.group(2).strip()

            current_rule = make_record(
                "规范条目", topic_name, text
            )
            records.append(current_rule)
            continue

        # 识别字体、字号、字形和颜色要求
        matched_field = False

        for field_name, pattern in field_patterns.items():
            match = pattern.match(text)

            if match:
                value = match.group(1).strip()

                if current_rule is not None:
                    current_rule[field_name] = value
                    current_rule["原始内容"].append(text)
                else:
                    # 没有明确的规范条目时，不擅自归类
                    pending = make_record(
                        "待确认内容", "待确认归属", text
                    )
                    pending[field_name] = value
                    pending["待确认"].append(
                        "发现格式要求，但前面没有明确的规范条目。"
                    )
                    records.append(pending)

                matched_field = True
                break

        if matched_field:
            continue

        # 特殊说明单独保留，不误认为字体或字号要求
        if text.startswith(("【特殊说明", "[特殊说明", "（特殊说明")):
            note = make_record(
                "特殊说明", "特殊说明", text
            )
            note["待确认"].append(
                "这是一条说明文字，不自动视为格式规范。"
            )
            records.append(note)
            continue

        # 其他普通段落独立保存，不擅自附加到上一条规范
        pending = make_record(
            "待确认内容", "待确认归属", text
        )
        pending["待确认"].append(
            "无法根据当前规则确定该段落的具体归属。"
        )
        records.append(pending)

    return records
