# DocPrep

面向 RAG 知识库的文档预处理工具。

## 1. 项目简介

DocPrep 是一个基于 Python 和 Streamlit 开发的文档预处理工具，旨在将不同格式的文档转换为结构化知识片段，为后续 RAG（检索增强生成）知识库的构建提供数据准备支持。

## 2. 主要功能

- **Word 解析**：提取段落、表格及部分文字格式信息，支持章节识别与知识分块。
- **Excel 解析**：按工作表和数据行提取结构化内容，保留工作表名称、行号等来源信息。
- **PDF 解析**：提取文本型 PDF 的内容，保留原始页码，支持按页拆分长文本。
- **TXT 解析**：支持常见中文编码，识别章节标题及正文，保留章节归属。
- **Markdown 解析**：识别多级标题和正文，避免将代码块中的 `#` 误判为标题。
- **知识块导出**：支持 JSON 和 Markdown 两种格式，保留内容、来源和元数据。

## 3. 技术栈

- Python 3.14
- Streamlit
- python-docx
- openpyxl
- PyMuPDF
- unittest

## 4. 安装与运行

创建并激活 Python 虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

安装项目依赖：

```powershell
python -m pip install -r requirements.txt
```

启动 DocPrep：

```powershell
python -m streamlit run app.py
```

在浏览器中打开 Streamlit 提供的本地访问地址，通常为：

`http://localhost:8501`

## 5. 运行测试

在项目根目录执行：

```powershell
python -m unittest discover -s . -p "test_*.py" -v
```

当前版本已完成 77 项自动化测试，最近一次运行全部通过。

## 6. 当前限制

- 暂不支持扫描版 PDF 的 OCR 文字识别。
- 对复杂排版文档的结构识别能力有限。
- TXT 主要识别符合指定规则的章节标题。
- 当前版本主要负责文档预处理，不包含向量数据库、Embedding 或完整的 RAG 问答服务。

## 7. 项目状态

DocPrep V1.0 已完成 Word、Excel、PDF、TXT 和 Markdown 五种文件格式的基础处理与导出功能，并通过基础端到端验收。