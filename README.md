# 基于大模型的 PPT 自动生成系统

## 项目简介

本项目是一个面向毕业设计答辩展示的 PPT 自动生成系统。系统不是简单调用大模型直接输出文本，而是支持用户上传参考资料，先解析资料并写入 Chroma 向量库，再根据 PPT 主题检索相关片段，将检索结果作为上下文交给大模型生成可编辑大纲，最后使用 python-pptx 和模板导出 PPT 文件。

## 技术栈

- 后端：FastAPI、SQLAlchemy、MySQL、JWT
- 前端：原生 HTML / CSS / JavaScript
- 大模型：LangChain、通义千问 / OpenAI 兼容模型
- RAG：Chroma、Embedding、文本切分、metadata 过滤
- PPT：python-pptx、PPT 母版模板、自动配图
- 图片：Pexels / Unsplash，可选

## 系统功能

- 用户注册、登录、JWT 鉴权
- 积分余额、充值套餐、模拟支付、订单记录
- 上传 txt、md、pdf、docx、pptx 参考资料
- 文件解析、文本切分、Chroma 向量入库
- 根据用户、文件和主题检索相关资料片段
- 生成 PPT 大纲并支持二次编辑
- 选择模板、自动配图、导出 pptx
- PPT 生成进度、失败原因、历史记录和文件下载

## 项目结构

```text
LLM_PPT_Generator/
├─ backend/
│  ├─ main.py              # FastAPI 路由入口
│  ├─ models.py            # SQLAlchemy ORM
│  ├─ schemas.py           # Pydantic 请求/响应模型
│  ├─ security.py          # 密码哈希与 JWT
│  └─ services/
├─ frontend/
│  ├─ index.html
│  ├─ styles.css
│  └─ app.js
├─ services/
│  ├─ file_parser_service.py
│  ├─ retrieval_service.py
│  ├─ outline_service.py
│  ├─ ppt_service.py
│  ├─ template_service.py
│  └─ image_service.py
├─ models/
│  └─ ppt_schema.py
├─ database/
│  ├─ schema.sql
│  └─ upgrade_rag_outline.sql
├─ templates/
├─ config/
│  └─ settings.py
├─ .env.example
├─ requirements.txt
└─ README.md
```

## 环境变量配置

复制 `.env.example` 为 `.env`，然后填写本地配置。敏感信息不要写进代码。

```powershell
Copy-Item .env.example .env
```

关键字段：

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=replace-with-your-mysql-password
MYSQL_DATABASE=llm_ppt_generator
JWT_SECRET_KEY=replace-with-a-long-random-secret
DASHSCOPE_API_KEY=replace-with-your-dashscope-api-key
```

如果使用 OpenAI 兼容接口，可调整：

```env
LLM_PROVIDER=openai_compatible
CHAT_MODEL_NAME=your-model-name
LLM_BASE_URL=https://your-compatible-endpoint/v1
LLM_API_KEY_ENV=OPENAI_API_KEY
OPENAI_API_KEY=replace-with-your-api-key
```

## 安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

如果 PowerShell 阻止激活虚拟环境：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 数据库初始化

新建数据库和表：

```powershell
mysql -u root -p < database/schema.sql
```

已有旧版本数据库时执行增量脚本：

```powershell
mysql -u root -p llm_ppt_generator < database/upgrade_rag_outline.sql
```

## 启动方式

项目保持原运行方式：

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问：

- 前端页面：http://127.0.0.1:8000
- API 文档：http://127.0.0.1:8000/docs

## PPT 生成流程

1. 用户注册并登录。
2. 系统读取 JWT，展示当前用户和积分余额。
3. 用户输入 PPT 主题、场景、页数、风格，选择模板和是否自动配图。
4. 用户上传参考资料，系统解析文本并写入向量库。
5. 用户点击“生成大纲”，后端检索相关资料并调用大模型生成 JSON 大纲。
6. 前端展示每页标题、版式、要点、讲稿备注，用户可以二次编辑。
7. 用户点击“确认生成 PPT”，后端根据最终大纲渲染 PPT。
8. 导出成功后扣除积分，写入历史记录，返回下载链接。

## RAG 检索增强流程

1. 上传资料保存到 `output/uploaded_files/`，文件基础信息写入 `uploaded_files` 表。
2. `FileParserService` 按格式提取文本：txt/md 直接读取，pdf 使用 pypdf，docx 使用 python-docx，pptx 使用 python-pptx。
3. `RetrievalService` 将文本切分为多个 chunk，写入 Chroma，并在 metadata 中记录 `user_id`、`file_id`、`source`。
4. 生成大纲时，系统按当前用户、上传文件 ID 和 PPT 主题检索 top-k 片段。
5. 检索结果与用户手动补充资料一起进入大模型提示词，提高内容与参考资料的一致性。

## 模板说明

前端通过下拉框选择模板，不再手动输入服务器路径。当前模板 ID：

- default：默认模板
- academic：学术答辩模板
- business：商务汇报模板
- tech_blue：科技蓝白模板
- minimal_bw：简约黑白模板

模板文件放在 `templates/` 目录，例如：

```text
templates/default_master.pptx
templates/academic_master.pptx
```

如果某个模板文件不存在，系统会自动回退默认模板；默认模板也不存在时使用空白 16:9 宽屏文稿，不会导致生成崩溃。

## 答辩展示流程

1. 注册并登录，展示 JWT 鉴权后的用户信息。
2. 进入 PPT 生成页，确认积分余额。
3. 输入主题：`基于大模型的 PPT 自动生成系统`。
4. 选择场景：毕业答辩；页数：8；风格：科技蓝白；模板：学术答辩模板。
5. 上传 txt、pdf 或 docx 参考资料。
6. 展示文件解析状态和知识库构建结果。
7. 点击生成大纲，展示 RAG 检索增强后的可编辑 JSON 大纲。
8. 修改其中一页标题或要点。
9. 点击确认生成 PPT，观察进度区域。
10. 生成完成后下载 pptx。
11. 切换历史记录，展示刚生成的 PPT 和下载入口。

答辩时可重点说明：本系统先解析用户上传资料，再通过向量检索获取相关内容，最后将检索结果作为上下文输入大模型生成 PPT 大纲，因此内容更贴合用户资料，而不是普通聊天式生成。
