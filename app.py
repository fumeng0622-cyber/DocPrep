
import json
from io import BytesIO
from dataclasses import replace

import streamlit as st
from docx import Document

from chunk_builder import build_chunks, split_long_text
from excel_parser import parse_xlsx
from pdf_parser import parse_pdf
from text_parser import parse_txt, parse_markdown
from knowledge_processor import attach_section_context
from rule_extractor import extract_rules
from word_parser import parse_docx


st.set_page_config(
    page_title="DocPrep - 文档预处理器",
    page_icon="📄",
    layout="wide",
)


def get_run_format(run, paragraph_style):
    """读取文字片段的格式，并尝试沿段落样式链查找。"""

    def find_format(property_name):
        value = getattr(run.font, property_name)
        if value is not None:
            return value, "文字片段直接设置"

        style = paragraph_style
        while style is not None:
            value = getattr(style.font, property_name)
            if value is not None:
                return value, f"来自样式：{style.name}"
            style = style.base_style

        return None, "未找到明确设置"

    font_name, font_source = find_format("name")
    font_size, size_source = find_format("size")
    bold, bold_source = find_format("bold")
    color, color_source = find_format("color")

    if font_name is not None:
        font_name = f"{font_name}（{font_source}）"
    else:
        font_name = font_source

    if font_size is not None:
        font_size = f"{font_size.pt:g} pt（{size_source}）"
    else:
        font_size = size_source

    if bold is True:
        bold = f"是（{bold_source}）"
    elif bold is False:
        bold = f"否（{bold_source}）"
    else:
        bold = bold_source

    if color is not None and color.rgb is not None:
        font_color = f"RGB #{color.rgb}（{color_source}）"
    else:
        font_color = "未找到明确的 RGB 颜色，可能使用主题色"

    return {
        "字体": font_name,
        "字号": font_size,
        "加粗": bold,
        "字体颜色": font_color,
    }


def chunks_to_json(chunks):
    """把知识片段转换成 JSON 字符串。"""
    return json.dumps(
        [chunk.to_dict() for chunk in chunks],
        ensure_ascii=False,
        indent=2,
    )


def chunks_to_markdown(chunks):
    """把知识片段转换成 Markdown 字符串。"""
    markdown_parts = []

    for index, chunk in enumerate(chunks, start=1):
        subsection = chunk.metadata.get("subsection")

        markdown_parts.append(
            f"## 知识片段 {index}\n\n"
            f"**一级章节：** {chunk.section or '未识别'}\n\n"
            f"**二级标题：** {subsection or '未识别'}\n\n"
            f"**内容类型：** "
            f"{chunk.metadata.get('element_type', '未知')}\n\n"
            f"{chunk.content}\n\n"
            f"**来源文件：** {chunk.source_file}\n\n"
            f"**来源类型：** {chunk.source_type}"
            + (f"\n\n**来源页码：** {chunk.page_number}" if chunk.page_number is not None else "")
        )

    return "\n\n---\n\n".join(markdown_parts)


def show_download_buttons(chunks, filename_prefix):
    """提供 JSON 和 Markdown 下载按钮。"""
    json_data = chunks_to_json(chunks)
    markdown_data = chunks_to_markdown(chunks)

    col_json, col_md = st.columns(2)

    with col_json:
        st.download_button(
            "下载 JSON",
            data=json_data,
            file_name=f"{filename_prefix}.json",
            mime="application/json",
            key=f"{filename_prefix}_json",
        )

    with col_md:
        st.download_button(
            "下载 Markdown",
            data=markdown_data,
            file_name=f"{filename_prefix}.md",
            mime="text/markdown",
            key=f"{filename_prefix}_md",
        )


st.title("📄 DocPrep")
st.subheader("面向 RAG 知识库的文档预处理器")

st.write(
    "上传 Word、Excel、PDF、TXT 或 Markdown 文件，提取内容和来源信息，"
    "并生成适合 RAG 知识库使用的知识块。"
)

st.divider()

st.header("第一步：上传文档")

uploaded_file = st.file_uploader(
    "请选择 Word、Excel、PDF、TXT 或 Markdown 文件",
    type=["docx", "xlsx", "pdf", "txt", "md"],
)

if uploaded_file is not None:
    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
    if extension == "docx":
        try:
            file_bytes = uploaded_file.getvalue()
            document = Document(BytesIO(file_bytes))

            st.success(f"文件上传成功：{uploaded_file.name}")

            paragraphs = [
                paragraph
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]

            # 第二步：提取文档内容与格式
            st.header("第二步：文档内容与格式提取")
            st.write(f"共提取到 {len(paragraphs)} 个非空段落。")

            for index, paragraph in enumerate(paragraphs, start=1):
                with st.expander(
                    f"段落 {index}：{paragraph.text[:50]}"
                ):
                    st.write("**段落内容**")
                    st.write(paragraph.text)

                    st.write(
                        f"**段落样式：** {paragraph.style.name}"
                    )

                    runs = [
                        run
                        for run in paragraph.runs
                        if run.text
                    ]

                    if not runs:
                        st.caption(
                            "该段落没有可读取的文字片段。"
                        )
                        continue

                    st.write("**文字片段格式**")

                    for run_index, run in enumerate(
                        runs,
                        start=1
                    ):
                        st.markdown(
                            f"**文字片段 {run_index}：** {run.text}"
                        )

                        st.json(
                            get_run_format(
                                run,
                                paragraph.style
                            )
                        )

            st.divider()

            # 第三步：识别公文格式规则
            st.header("第三步：规则识别结果")

            paragraph_texts = [
                paragraph.text
                for paragraph in paragraphs
            ]

            rules = extract_rules(paragraph_texts)

            if rules:
                st.write(
                    f"共整理出 {len(rules)} 条候选记录。"
                )

                for index, rule in enumerate(rules, start=1):
                    with st.expander(
                        f"候选记录 {index}：{rule['规范名称']}"
                    ):
                        st.json(rule)
            else:
                st.info("暂未识别到候选规则。")

            st.divider()

            # 第四步：通用知识解析
            st.header("第四步：通用知识解析结果")

            chunks = parse_docx(
                file_bytes,
                uploaded_file.name
            )

            chunks = attach_section_context(chunks)

            if chunks:
                st.success(
                    f"成功提取 {len(chunks)} 条知识片段。"
                )

                show_download_buttons(
                    chunks,
                    "docprep_knowledge"
                )

                paragraph_count = sum(
                    1
                    for chunk in chunks
                    if chunk.metadata.get("element_type")
                    == "paragraph"
                )

                table_row_count = sum(
                    1
                    for chunk in chunks
                    if chunk.metadata.get("element_type")
                    == "table_row"
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        "正文段落",
                        paragraph_count
                    )

                with col2:
                    st.metric(
                        "表格行",
                        table_row_count
                    )

                for index, chunk in enumerate(
                    chunks,
                    start=1
                ):
                    element_type = chunk.metadata.get(
                        "element_type"
                    )

                    type_name = (
                        "表格"
                        if element_type == "table_row"
                        else "段落"
                    )

                    with st.expander(
                        f"知识片段 {index}（{type_name}）："
                        f"{chunk.content[:40]}"
                    ):
                        st.write("**知识内容**")
                        st.write(chunk.content)

                        st.write("**所属章节**")
                        st.write(
                            chunk.section or "未识别到章节"
                        )

                        st.write("**二级标题**")
                        st.write(
                            chunk.metadata.get("subsection")
                            or "未识别到二级标题"
                        )

                        st.write("**来源文件**")
                        st.write(chunk.source_file)

                        st.write("**元数据**")
                        st.json(chunk.metadata)

                st.divider()

                # 第五步：智能知识分块
                st.header("第五步：智能知识分块结果")

                st.write(
                    "根据章节结构合并相邻正文，"
                    "并对超长内容进行拆分。"
                )

                col_max, col_overlap = st.columns(2)

                with col_max:
                    max_chars = st.number_input(
                        "每个知识块的最大字符数",
                        min_value=100,
                        max_value=5000,
                        value=800,
                        step=100,
                    )

                with col_overlap:
                    overlap = st.number_input(
                        "重叠字符数",
                        min_value=0,
                        max_value=500,
                        value=100,
                        step=50,
                    )

                if overlap >= max_chars:
                    st.warning(
                        "重叠字符数必须小于最大字符数，"
                        "请调整参数。"
                    )
                else:
                    merged_chunks = build_chunks(
                        chunks,
                        max_chars=int(max_chars),
                        overlap=int(overlap),
                    )

                    st.success(
                        f"分块完成，共生成 "
                        f"{len(merged_chunks)} 条知识片段。"
                    )

                    show_download_buttons(
                        merged_chunks,
                        "docprep_chunked"
                    )

                    merged_text_count = sum(
                        1
                        for chunk in merged_chunks
                        if chunk.metadata.get("element_type")
                        == "merged_text"
                    )

                    col_before, col_after, col_merged = (
                        st.columns(3)
                    )

                    with col_before:
                        st.metric(
                            "分块前片段数",
                            len(chunks)
                        )

                    with col_after:
                        st.metric(
                            "分块后片段数",
                            len(merged_chunks)
                        )

                    with col_merged:
                        st.metric(
                            "正文知识块数",
                            merged_text_count
                        )

                    st.caption(
                        "分块后片段数包含独立保留的标题、"
                        "表格行和合并后的正文知识块。"
                    )

                    for index, chunk in enumerate(
                        merged_chunks,
                        start=1
                    ):
                        element_type = chunk.metadata.get(
                            "element_type"
                        )

                        if element_type == "merged_text":
                            type_name = "合并正文"
                        elif element_type == "table_row":
                            type_name = "表格"
                        elif chunk.metadata.get(
                            "heading_level"
                        ) is not None:
                            type_name = "标题"
                        else:
                            type_name = "其他"

                        char_count = len(chunk.content)

                        with st.expander(
                            f"知识块 {index}（{type_name}，"
                            f"{char_count} 字符）："
                            f"{chunk.content[:35]}"
                        ):
                            st.write("**知识内容**")
                            st.write(chunk.content)

                            st.write("**字符数**")
                            st.write(char_count)

                            st.write("**一级章节**")
                            st.write(
                                chunk.section or "未识别"
                            )

                            st.write("**二级标题**")
                            st.write(
                                chunk.metadata.get("subsection")
                                or "未识别"
                            )

                            st.write("**来源文件**")
                            st.write(chunk.source_file)

                            st.write("**元数据**")
                            st.json(chunk.metadata)

            else:
                st.info(
                    "文档中没有可提取的正文或表格内容。"
                )

        except Exception as error:
            st.error(
                "文档处理失败，请检查文件格式或处理参数。"
            )
            st.exception(error)

    elif extension == "xlsx":
        try:
            file_bytes = uploaded_file.getvalue()
            chunks = parse_xlsx(file_bytes, uploaded_file.name)
            st.success(f"文件上传成功：{uploaded_file.name}")

            st.header("第二步：Excel 数据提取")
            if not chunks:
                st.info("未提取到数据行。请检查工作表是否有表头和数据。")
            else:
                sheet_names = list(dict.fromkeys(
                    chunk.metadata.get("sheet_name", "未命名工作表")
                    for chunk in chunks
                ))
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("包含数据的工作表", len(sheet_names))
                with col2:
                    st.metric("提取的数据行", len(chunks))
                st.caption("默认每个工作表的第一行是表头，从第二行开始提取数据。")

                st.header("第三步：Excel 知识块预览")
                for index, chunk in enumerate(chunks, start=1):
                    sheet_name = chunk.metadata.get("sheet_name", "未命名工作表")
                    row_number = chunk.metadata.get("row_number", "未知")
                    with st.expander(
                        f"记录 {index}｜{sheet_name}｜第 {row_number} 行：{chunk.content[:35]}"
                    ):
                        st.text(chunk.content)
                        st.write("**来源文件：**", chunk.source_file)
                        st.json(chunk.metadata)

                st.header("第四步：导出原始 Excel 知识块")
                show_download_buttons(chunks, "docprep_excel_knowledge")

                st.header("第五步：Excel 分块结果")
                st.info(
                    "Excel 数据按行独立保留，不进行 Word 正文式合并。"
                    "当前版本不拆分超长表格行，以免破坏单条记录。"
                )
                # build_chunks 对非 paragraph 类型直接保留，不会合并 excel_row。
                result_chunks = build_chunks(chunks)
                st.success(f"共保留 {len(result_chunks)} 条独立知识块。")
                show_download_buttons(result_chunks, "docprep_excel_chunked")
        except Exception as error:
            st.error("Excel 处理失败，请检查文件格式。")
            st.exception(error)
    elif extension == "pdf":
        try:
            file_bytes = uploaded_file.getvalue()
            chunks = parse_pdf(file_bytes, uploaded_file.name)
            st.success(f"文件上传成功：{uploaded_file.name}")

            st.header("第二步：PDF 文字提取")
            if not chunks:
                st.warning(
                    "没有提取到可复制的文字。文件可能是扫描版 PDF，"
                    "当前版本暂不支持 OCR 识别。"
                )
            else:
                col_pages, col_chars = st.columns(2)
                with col_pages:
                    st.metric("提取到文字的页数", len(chunks))
                with col_chars:
                    st.metric("提取字符数", sum(len(c.content) for c in chunks))
                st.caption("按原始页码提取；空白页会跳过。暂不处理复杂排版及扫描件。")

                st.header("第三步：PDF 原始知识块预览")
                for index, chunk in enumerate(chunks, start=1):
                    with st.expander(
                        f"片段 {index}｜第 {chunk.page_number} 页｜"
                        f"{len(chunk.content)} 字符：{chunk.content[:35]}"
                    ):
                        st.text(chunk.content)
                        st.write("**来源文件：**", chunk.source_file)
                        st.json(chunk.metadata)

                st.header("第四步：导出原始 PDF 知识块")
                show_download_buttons(chunks, "docprep_pdf_knowledge")

                st.header("第五步：PDF 智能分块")
                st.write("按页拆分长文本，每个子块保留原始页码，不跨页合并。")
                col_max, col_overlap = st.columns(2)
                with col_max:
                    max_chars = st.number_input(
                        "每块最大字符数", min_value=100, max_value=5000,
                        value=800, step=100, key="pdf_max_chars"
                    )
                with col_overlap:
                    overlap = st.number_input(
                        "重叠字符数", min_value=0, max_value=500,
                        value=100, step=50, key="pdf_overlap"
                    )

                if overlap >= max_chars:
                    st.warning("重叠字符数必须小于每块最大字符数。")
                else:
                    result_chunks = []
                    for chunk in chunks:
                        parts = split_long_text(
                            chunk.content, max_chars=int(max_chars),
                            overlap=int(overlap)
                        )
                        for part_index, part in enumerate(parts, start=1):
                            metadata = chunk.metadata.copy()
                            metadata.update({
                                "element_type": "pdf_text_chunk",
                                "part_number": part_index,
                                "part_count": len(parts),
                                "char_count": len(part),
                            })
                            result_chunks.append(replace(
                                chunk, content=part, metadata=metadata
                            ))

                    st.success(f"分块完成，共生成 {len(result_chunks)} 条知识块。")
                    show_download_buttons(result_chunks, "docprep_pdf_chunked")
                    for index, chunk in enumerate(result_chunks, start=1):
                        with st.expander(
                            f"知识块 {index}｜第 {chunk.page_number} 页｜"
                            f"{len(chunk.content)} 字符：{chunk.content[:35]}"
                        ):
                            st.text(chunk.content)
                            st.json(chunk.metadata)
        except Exception as error:
            st.error("PDF 处理失败，请检查文件格式或分块参数。")
            st.exception(error)
    elif extension in ("txt", "md"):
        try:
            file_bytes = uploaded_file.getvalue()
            if extension == "txt":
                chunks = parse_txt(file_bytes, uploaded_file.name)
                format_name = "TXT"
            else:
                chunks = parse_markdown(file_bytes, uploaded_file.name)
                format_name = "Markdown"

            st.success(f"文件上传成功：{uploaded_file.name}")
            st.header(f"第二步：{format_name} 内容提取")
            if not chunks:
                st.info("文件为空，或没有可提取的文本内容。")
            else:
                st.metric("原始知识片段数", len(chunks))
                st.header("第三步：原始知识片段预览")
                for index, chunk in enumerate(chunks, start=1):
                    kind = chunk.metadata.get("element_type", "未知")
                    with st.expander(
                        f"片段 {index}｜{kind}｜{len(chunk.content)} 字符：{chunk.content[:35]}"
                    ):
                        st.text(chunk.content)
                        st.write("**所属章节：**", chunk.section or "未识别")
                        st.write("**二级标题：**", chunk.metadata.get("subsection") or "未识别")
                        st.json(chunk.metadata)

                st.header("第四步：导出原始知识片段")
                show_download_buttons(chunks, f"docprep_{extension}_knowledge")

                st.header("第五步：智能知识分块")
                st.caption("标题单独保留；正文超长时拆分，并保留来源和章节信息。")
                col_max, col_overlap = st.columns(2)
                with col_max:
                    max_chars = st.number_input(
                        "每块最大字符数", min_value=100, max_value=5000,
                        value=800, step=100, key=f"{extension}_max_chars"
                    )
                with col_overlap:
                    overlap = st.number_input(
                        "重叠字符数", min_value=0, max_value=500,
                        value=100, step=50, key=f"{extension}_overlap"
                    )

                if overlap >= max_chars:
                    st.warning("重叠字符数必须小于每块最大字符数。")
                else:
                    result_chunks = []
                    for chunk in chunks:
                        if chunk.metadata.get("element_type") == "heading":
                            result_chunks.append(chunk)
                            continue
                        parts = split_long_text(
                            chunk.content,
                            max_chars=int(max_chars),
                            overlap=int(overlap),
                        )
                        for part_index, part in enumerate(parts, start=1):
                            metadata = chunk.metadata.copy()
                            metadata.update({
                                "element_type": "text_chunk",
                                "part_number": part_index,
                                "part_count": len(parts),
                                "char_count": len(part),
                            })
                            result_chunks.append(replace(
                                chunk, content=part, metadata=metadata
                            ))

                    st.success(f"分块完成，共生成 {len(result_chunks)} 条知识块。")
                    show_download_buttons(result_chunks, f"docprep_{extension}_chunked")
                    for index, chunk in enumerate(result_chunks, start=1):
                        with st.expander(
                            f"知识块 {index}｜{len(chunk.content)} 字符：{chunk.content[:35]}"
                        ):
                            st.text(chunk.content)
                            st.write("**所属章节：**", chunk.section or "未识别")
                            st.json(chunk.metadata)
        except Exception as error:
            st.error(f"{extension.upper()} 处理失败，请检查文件内容或分块参数。")
            st.exception(error)
    else:
        st.error("暂不支持该文件类型。")

else:
    st.caption("请先选择一个 .docx、.xlsx、.pdf、.txt 或 .md 文件进行测试。")
