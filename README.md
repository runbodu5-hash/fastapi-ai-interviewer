# fastapi-ai-interviewer
A high-performance, asynchronous AI technical screening system based on FastAPI and LangChain, featuring Parent-Child RAG and stream interaction.
Why I Built This
I built this project to solve production-level challenges in LLM deployment, specifically focusing on RAG accuracy, memory management under high concurrency, cost control, and prompt injection vulnerabilities during multi-turn technical interviews.

基于 FastAPI + LangChain 的多轮 AI 技术初筛系统 🚀
1. 项目介绍 (Project Introduction)
本项目是一款专门面向现代化招聘与技术初筛场景自研的前后端分离式对话原型系统。项目针对大模型（LLM）在实际工业落地中暴露出的典型工程痛点——如长文本切片检索失真、高并发下服务器内存积压（OOM）、客户端异常断连导致算力资源空转白耗，以及恶意提示词注入越狱等问题，进行了深度的工程底座设计与架构优化，完整实现了“简历灌入-高精语义匹配-多轮流式对话-安全风险拦截-评估报告落盘”的闭环业务流程。

2. 功能列表 (Feature List)

🔍 双层检索：采用 LangChain 实现 Parent-Child 父子双层文本切片，基于 Chroma 向量数据库进行子块高精语义检索，并通过 UUID 异步召回大粒度父块补全上下文，解决传统长文本检索精度低与上下文缺失的痛点。

⚡ 异步流式：基于 FastAPI 异步协程架构与 yield 机制，将大模型输出碎字实时推送至前端缓冲区，严格控制单次请求的瞬时内存开销，防止高并发场景下服务器出现 OOM 内存溢出。

🛡️ 断连熔断：深度捕获底层 asyncio.CancelledError 异常信号，在网页端异常关闭或断连时实现秒级熔断，自动终止大模型网络长连接并清理后台空转的僵尸协程，严控 API Token 算力成本。

🔒 安全清洗：搭建路由前置的轻量化 WAF 清洗模块，利用正则表达式全局过滤并标准化用户输入内容，在请求进入模型前安全拦截恶意特殊闭合标签，防范提示词注入与 AI 角色篡改攻击。

💾 异步落盘：调用 aiofiles 模块实现多轮会话本地 JSON 账本的异步读写，避免常驻内存开销；会话结束后自动调用模型生成 Markdown 格式技术评估报告，并配置前端数据流式一键下载。

3. 安装步骤 (Installation Steps)请确保您的本地开发环境已安装 Python 3.10+ 并配置好相关网络代理。克隆项目仓库Bashgit clone https://github.com/runbodu5-hash/fastapi-langchain-screener.git
cd fastapi-langchain-screener
创建并激活虚拟环境Bashpython -m venv langchain_v1_env
# Windows 激活命令:
langchain_v1_env\Scripts\activate
# macOS/Linux 激活命令:
source langchain_v1_env/bin/activate
安装项目依赖Bashpip install -r requirements.txt
配置环境变量在项目根目录下创建一个 .env 文件，并配置您的 API 密钥与基础路径：代码段DEEPSEEK_API_KEY=your_deepseek_api_key_here
BASE_URL=https://api.deepseek.com/v1
4. 使用说明 (Usage Instructions)启动后端 FastAPI 服务在激活的虚拟环境中执行以下命令启动 Uvicorn 高性能服务器：Bashuvicorn main:app --host 127.0.0.1 --port 8000 --reload
启动前端 Streamlit 原型打开另一个终端窗口，激活虚拟环境并运行：Bashstreamlit run ui.py
全链路业务体验打开浏览器访问 Streamlit 生成的本地地址（通常为 http://localhost:8501）。通过前端上传一份技术简历，系统将自动触发 Parent-Child 切片并灌入 Chroma 向量数据库。进入多轮流式对话界面，系统将模拟技术面试官进行针对性提问，并在会话结束后支持一键导出 Markdown 格式的技术评估报告。5. 项目结构 (Project Structure)Plaintextfastapi-langchain-screener/
├── .env                 # 环境变量配置文件（存储 API Key 及 Base URL）
├── .gitignore           # Git 忽略文件列表
├── README.md            # 项目技术说明文档
├── main.py              # FastAPI 后端核心路由与异步协程网关
├── ui.py                # Streamlit 前端交互与打字机流式吞吐界面
├── requirements.txt     # 项目核心依赖依赖包管理文件
├── config/
│   └── security_waf.py  # 前置安全清洗模块（正则防御提示词注入）
└── services/
    ├── __init__.py
    ├── rag_engine.py    # LangChain + Chroma 父子双层切片检索模块
    └── session_mgr.py   # 基于 aiofiles 的会话 JSON 异步落盘服务
6. 截图占位符 (Screenshot Placeholders)后端异步流式控制台 (FastAPI & Uvicorn)前端 AI 智能初筛交互 (Streamlit UII)

7. MIT License 说明 (MIT License Notice)
本项目采用 MIT License 开源协议。您可以自由地复制、修改、分发及用于商业或个人目的，但请务必在修改后的核心代码或衍生文件中保留原作者的版权声明与许可声明。详情请参见项目根目录下的 LICENSE 文件。
