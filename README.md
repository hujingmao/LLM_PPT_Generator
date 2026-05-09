# 基于大模型的 PPT 自动生成系统

## 1. 项目简介

本项目采用前后端分离架构，将“主题输入、资料增强、PPT 规划、模板排版、积分扣费、文件下载”串成一套完整的 PPT 自动生成系统。

- 后端：FastAPI + SQLAlchemy + MySQL
- 前端：原生 HTML / CSS / JavaScript 静态页面
- 大模型：LangChain + 通义千问 / OpenAI 兼容模型
- PPT：python-pptx + 模板母版 + 自动配图

## 2. 功能介绍

- 用户注册、登录、JWT 鉴权。
- 积分余额、充值套餐、模拟支付和充值订单记录。
- 输入主题后自动生成 PPT 标题、副标题、页面规划和讲稿备注。
- 支持从 `.pptx` 母版模板生成商业化版式。
- 支持 Pexels / Unsplash 图片 API 自动配图。
- 保存 PPT 生成记录，并支持历史文件下载。

## 3. 项目结构

```bash
LLM_PPT_Generator/
├─ backend/
│  ├─ main.py
│  ├─ models.py
│  ├─ schemas.py
│  ├─ security.py
│  └─ services/
├─ frontend/
│  ├─ index.html
│  ├─ styles.css
│  └─ app.js
├─ database/
│  └─ schema.sql
├─ config/
│  └─ settings.py
├─ services/
│  ├─ llm_service.py
│  ├─ retrieval_service.py
│  ├─ outline_service.py
│  ├─ ppt_service.py
│  ├─ image_service.py
│  └─ file_parser_service.py
├─ models/
│  └─ ppt_schema.py
├─ templates/
│  └─ README.md
├─ output/
│  └─ generated_ppt/
├─ chroma_db/
├─ knowledge_base.py
├─ vector_stores.py
├─ model_factory.py
├─ config_data.py
└─ requirements.txt
```

## 4. 安装依赖

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
```

如果 PowerShell 阻止激活虚拟环境，可先运行：

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 5. 初始化数据库

先确保 MySQL 服务已启动，然后执行：

```bash
mysql -u root -p < database/schema.sql
```

## 6. 配置环境变量

Windows PowerShell 示例：

```bash
$env:DATABASE_URL="mysql+pymysql://root:你的密码@127.0.0.1:3306/llm_ppt_generator?charset=utf8mb4"
$env:JWT_SECRET_KEY="请替换成足够长的随机字符串"
$env:DASHSCOPE_API_KEY="你的通义千问 API Key"
```

自动配图可任选其一：

```bash
$env:PEXELS_API_KEY="你的 Pexels API Key"
$env:UNSPLASH_ACCESS_KEY="你的 Unsplash Access Key"
```

也可以参考 `.env.example` 统一维护配置。

## 7. 启动项目

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问：

- 前端页面：http://127.0.0.1:8000
- API 文档：http://127.0.0.1:8000/docs

## 8. 模板机制

将商业母版放到：

```bash
templates/default_master.pptx
```

生成器会优先加载该模板，清空示例页并保留母版主题、尺寸和版式资源。接口 `/api/ppt/generate` 也支持传入 `template_path` 指定其他 `.pptx` 模板。
