# 基于大模型的 PPT 自动生成系统

## 1. 项目简介

本项目是一个基于 Streamlit 的毕业设计演示系统，目标是将传统“手工做 PPT”的流程升级为“主题驱动 + 参考资料增强 + 自动生成 `.pptx`”的一体化流程。  
系统基于现有 RAG 能力重构，支持输入主题、上传资料、自动生成结构化页面规划，并输出可下载的真实 PPT 文件。

## 2. 功能介绍

- 输入主题后自动生成 PPT 标题、副标题与页面规划。
- 支持上传参考资料（MVP 支持 `txt` / `md`）并进行检索增强。
- 输出结构化 JSON（含每页标题、要点、讲稿备注）。
- 自动生成封面、目录、内容页、总结页。
- 页面内直接下载 `.pptx` 文件。

## 3. 项目结构

```bash
LLM_PPT_Generator/
├─ app.py
├─ config/
│  └─ settings.py
├─ services/
│  ├─ llm_service.py
│  ├─ retrieval_service.py
│  ├─ outline_service.py
│  ├─ ppt_service.py
│  └─ file_parser_service.py
├─ models/
│  └─ ppt_schema.py
├─ utils/
│  ├─ json_utils.py
│  ├─ filename_utils.py
│  └─ logger.py
├─ output/
│  └─ generated_ppt/
├─ chroma_db/
├─ chat_history/
├─ knowledge_base.py
├─ vector_stores.py
├─ model_factory.py
├─ config_data.py
└─ requirements.txt
```

## 4. 安装步骤

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

## 5. 配置说明

本项目默认使用通义千问能力，需提前配置环境变量：

```bash
# 推荐：ChatTongyi + DashScopeEmbeddings
set DASHSCOPE_API_KEY=你的key
```

如需使用 OpenAI 兼容模式，可在 `config/settings.py` 中调整 `LLM_PROVIDER` 与相关参数。

## 6. 启动方式

```bash
streamlit run app.py
```

## 7. 使用说明

1. 输入 PPT 主题（必填）。
2. 选择场景、页数、风格。
3. 可选上传 `txt` / `md` 参考资料。
4. 点击“开始生成 PPT”。
5. 查看结构化规划与每页要点。
6. 下载系统生成的 `.pptx` 文件。

## 8. 后续可扩展方向

- 增加 `pdf/docx` 解析能力。
- 增加多套版式模板（商务、答辩、教学等）。
- 增加图片检索与插图生成。
- 增加讲稿导出（Word/Markdown）。
- 增加前后端分离部署形态（FastAPI + 前端框架）。

