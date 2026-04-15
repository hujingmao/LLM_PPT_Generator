import json

import streamlit as st

from config.settings import (
    DEFAULT_PAGE_COUNT,
    MAX_PAGE_COUNT,
    MIN_PAGE_COUNT,
)
from services.file_parser_service import FileParserService
from services.outline_service import OutlineService
from services.ppt_service import PPTService
from services.retrieval_service import RetrievalService


st.set_page_config(page_title="基于大模型的 PPT 自动生成系统", layout="wide")

st.title("基于大模型的 PPT 自动生成系统")
st.caption("输入主题或上传参考资料，自动生成演示文稿")
st.divider()

with st.sidebar:
    st.subheader("生成参数")
    scene = st.selectbox(
        "目标场景",
        ["课程汇报", "毕业答辩", "产品介绍", "工作汇报", "学术报告"],
        index=1,
    )
    page_count = st.slider("页数", min_value=MIN_PAGE_COUNT, max_value=MAX_PAGE_COUNT, value=DEFAULT_PAGE_COUNT)
    style = st.selectbox("风格", ["简洁商务", "学术答辩", "教学汇报"], index=1)
    use_retrieval = st.checkbox("启用参考资料检索增强", value=True)

topic = st.text_input("请输入 PPT 主题", placeholder="例如：基于大模型的 PPT 自动生成系统设计与实现")
uploaded_files = st.file_uploader(
    "上传参考资料（支持 txt / md，可多选）",
    type=["txt", "md"],
    accept_multiple_files=True,
)

if st.button("开始生成 PPT", type="primary"):
    if not topic.strip():
        st.warning("请先输入 PPT 主题。")
        st.stop()

    file_parser = FileParserService()
    retrieval_service = RetrievalService()
    outline_service = OutlineService()
    ppt_service = PPTService()

    with st.spinner("正在解析参考资料..."):
        parsed_docs = file_parser.parse_uploaded_files(uploaded_files or [])
        if uploaded_files and not parsed_docs:
            st.warning("上传文件为空或格式不支持，系统将仅基于主题生成。")

    retrieval_context = ""
    if use_retrieval and parsed_docs:
        with st.spinner("正在构建向量索引并检索上下文..."):
            ingest_logs = retrieval_service.ingest_documents(parsed_docs)
            for line in ingest_logs:
                st.caption(line)
            retrieval_context = retrieval_service.retrieve_context(topic, top_k=3)
    elif use_retrieval and not parsed_docs:
        st.warning("未检测到可用参考资料，自动切换为纯主题生成。")

    try:
        with st.spinner("正在生成 PPT 规划..."):
            plan = outline_service.generate_plan(
                topic=topic,
                scene=scene,
                page_count=page_count,
                style=style,
                retrieval_context=retrieval_context,
            )
        st.success("PPT 结构规划生成成功。")
    except Exception as exc:
        st.error(f"PPT 规划生成失败：{exc}")
        st.stop()

    try:
        with st.spinner("正在生成 .pptx 文件..."):
            output_path = ppt_service.generate_ppt(plan, topic=topic)
        st.success(f"PPT 文件生成成功：{output_path.name}")
    except Exception as exc:
        st.error(f"PPT 文件生成失败：{exc}")
        st.stop()

    st.subheader("生成结果")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**PPT 标题：** {plan.ppt_title}")
        st.markdown(f"**副标题：** {plan.subtitle}")
        st.markdown(f"**主题风格：** {plan.theme}")
    with col2:
        with open(output_path, "rb") as f:
            st.download_button(
                label="下载 PPT 文件",
                data=f.read(),
                file_name=output_path.name,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )

    st.markdown("### 结构化 JSON")
    st.code(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2), language="json")

    st.markdown("### 每页内容规划")
    for page in plan.pages:
        with st.expander(f"第 {page.page_no} 页 - {page.page_title}", expanded=False):
            st.write("要点：")
            for bullet in page.bullets:
                st.markdown(f"- {bullet}")
            st.write(f"讲稿备注：{page.speaker_notes or '无'}")

