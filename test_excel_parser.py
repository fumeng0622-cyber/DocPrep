
import unittest
from io import BytesIO

from openpyxl import Workbook

from excel_parser import parse_xlsx


def create_excel_bytes(sheet_data):
    """
    在内存中创建测试 Excel 文件。

    sheet_data:
    {
        "工作表名称": [
            ["表头1", "表头2"],
            ["数据1", "数据2"]
        ]
    }
    """

    workbook = Workbook()

    first_sheet = True

    for sheet_name, rows in sheet_data.items():

        if first_sheet:
            sheet = workbook.active
            sheet.title = sheet_name
            first_sheet = False
        else:
            sheet = workbook.create_sheet(sheet_name)

        for row in rows:
            sheet.append(row)

    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()

    return buffer.getvalue()


class ExcelParserTests(unittest.TestCase):

    def test_basic_excel_parsing(self):
        """测试基本 Excel 数据行解析。"""

        file_bytes = create_excel_bytes({
            "成绩表": [
                ["姓名", "科目", "成绩"],
                ["张三", "数学", 95],
                ["李四", "语文", 88],
            ]
        })

        result = parse_xlsx(file_bytes, "成绩表.xlsx")

        self.assertEqual(len(result), 2)

        self.assertEqual(
            result[0].content,
            "姓名：张三\n科目：数学\n成绩：95"
        )

        self.assertEqual(
            result[1].content,
            "姓名：李四\n科目：语文\n成绩：88"
        )

    def test_multiple_sheets(self):
        """测试多个工作表是否全部读取。"""

        file_bytes = create_excel_bytes({
            "语文": [
                ["姓名", "成绩"],
                ["张三", 90],
            ],
            "数学": [
                ["姓名", "成绩"],
                ["李四", 95],
            ],
        })

        result = parse_xlsx(file_bytes, "多工作表.xlsx")

        self.assertEqual(len(result), 2)

        self.assertEqual(
            result[0].metadata["sheet_name"],
            "语文"
        )

        self.assertEqual(
            result[1].metadata["sheet_name"],
            "数学"
        )

    def test_empty_rows_are_skipped(self):
        """测试完全为空的数据行会被跳过。"""

        file_bytes = create_excel_bytes({
            "Sheet1": [
                ["姓名", "成绩"],
                ["张三", 95],
                [None, None],
                ["李四", 88],
            ]
        })

        result = parse_xlsx(file_bytes, "空行测试.xlsx")

        self.assertEqual(len(result), 2)

        self.assertEqual(
            result[1].metadata["row_number"],
            4
        )

    def test_empty_cells_are_skipped(self):
        """测试空单元格不会生成无意义字段。"""

        file_bytes = create_excel_bytes({
            "Sheet1": [
                ["姓名", "科目", "成绩"],
                ["张三", None, 95],
            ]
        })

        result = parse_xlsx(file_bytes, "空单元格.xlsx")

        self.assertEqual(len(result), 1)

        self.assertEqual(
            result[0].content,
            "姓名：张三\n成绩：95"
        )

    def test_missing_headers(self):
        """测试空表头自动生成列名。"""

        file_bytes = create_excel_bytes({
            "Sheet1": [
                ["姓名", None, "成绩"],
                ["张三", "数学", 95],
            ]
        })

        result = parse_xlsx(file_bytes, "缺失表头.xlsx")

        self.assertEqual(len(result), 1)

        self.assertIn(
            "列2：数学",
            result[0].content
        )

    def test_metadata(self):
        """测试知识块来源信息是否正确。"""

        file_bytes = create_excel_bytes({
            "学生信息": [
                ["姓名", "年龄"],
                ["张三", 18],
            ]
        })

        result = parse_xlsx(file_bytes, "学生.xlsx")

        chunk = result[0]

        self.assertEqual(chunk.source_file, "学生.xlsx")
        self.assertEqual(chunk.source_type, "xlsx")
        self.assertEqual(chunk.title, "学生信息")
        self.assertEqual(chunk.section, "学生信息")

        self.assertEqual(
            chunk.metadata["element_type"],
            "excel_row"
        )

        self.assertEqual(
            chunk.metadata["row_number"],
            2
        )

        self.assertEqual(
            chunk.metadata["column_count"],
            2
        )


if __name__ == "__main__":
    unittest.main()
