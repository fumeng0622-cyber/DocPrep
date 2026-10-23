# DocPrep

DocPrep 是一个基于 Python 和 Streamlit 开发的文档预处理工具，主要用于将不同格式的文档转换为适合 RAG（检索增强生成）知识库使用的结构化知识片段。

## 1. 项目功能

目前支持五种文档格式：

| 格式 | 主要功能 |
|---|---|
| Word（DOCX） | 段落和表格提取、章节识别、智能分块 |
| Excel（XLSX） | 工作表解析、表头识别、数据行提取 |
| PDF | 文本提取、页码保留、长文本分块 |
| TXT | 文本编码兼容、内容提取、文本分块 |
| Markdown（MD） | 标题层级识别、章节关联、正文分块 |

其他功能：

- 通过 Streamlit 网页上传和预览文档。
- 统一使用 `KnowledgeChunk` 保存知识片段及来源信息。
- 支持配置最大分块字符数和重叠字符数。
- 支持将处理结果导出为 JSON 和 Markdown。
- 提供自动化测试，验证主要解析功能。

## 2. 技术栈

- Python
- Streamlit
- python-docx
- openpyxl
- PyMuPDF
- unittest

## 3. 安装与运行

### 3.1 创建虚拟环境

在项目根目录执行：

```powershell
python -m venv .venv
```

### 3.2 激活虚拟环境

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3.3 安装依赖

```powershell
python -m pip install -r requirements.txt
```

### 3.4 启动项目

```powershell
python -m streamlit run app.py
```

启动后，在浏览器中访问：

http://localhost:8501

## 4. 使用方法

1. 打开 DocPrep 网页。
2. 上传支持格式的文档。
3. 查看文档解析结果及知识片段。
4. 根据需要调整分块参数。
5. 下载 JSON 或 Markdown 处理结果。

## 5. 自动化测试

在项目根目录执行：

```powershell
python -m unittest discover -v
```

截至 V1.0 交付准备阶段，项目已有 61 个自动化测试通过。

## 6. 当前限制

- PDF 主要支持可提取文本的文档，暂不支持扫描件 OCR。
- 复杂 PDF 排版和表格暂未完整处理。
- Excel 默认第一行为表头，暂不完整支持复杂合并单元格。
- TXT 暂不自动识别章节结构。
- Markdown 主要支持常见的井号标题和基础正文结构。
- 尚未直接连接 Dify 或向量数据库。

## 7. 后续计划

- 通过 Dify API 自动上传预处理后的知识内容。
- 增强复杂文档解析能力。
- 支持批量文件处理。
- 完善来源元数据与知识库同步功能。

## 8. 版本

**V1.0.0 — 基础文档预处理版本**

包含五种文件格式的解析、知识分块、网页操作和结构化导出功能。
