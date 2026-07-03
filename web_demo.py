import streamlit as st
import requests

# =====================================================================
# 1. 基础配置与全局状态初始化
# =====================================================================
st.set_page_config(
    page_title="AI大厂技术面试初筛系统",
    page_icon="🤖",
    layout="wide"
)

BACKEND_BASE_URL = "http://127.0.0.1:8999"

# 确保前端会话中有一个持久化的聊天记录本
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =====================================================================
# 2. 侧边栏（Sidebar）- 账户管理、简历上传硬核舱门
# =====================================================================
with st.sidebar:
    st.title("⚙️ 招聘大厅控制台")
    st.subheader("1. 面试沙盒账户切换")

    # 模拟真实高并发多沙盒会话，切换账户会自动去后端捞对应的 JSON 记忆
    session_option = st.selectbox(
        "请选择当前求职者账户：",
        ("candidate_zhangsan", "candidate_lisi", "candidate_wangwu")
    )

    # 如果用户在前端切换了账户，自动清空当前前端浏览器的临时缓存，逼迫前端去后端拉取新的历史
    if "current_user" not in st.session_state or st.session_state.current_user != session_option:
        st.session_state.current_user = session_option
        st.session_state.chat_history = []  # 清空旧的前端视觉残留

    st.markdown("---")
    st.subheader("2. 简历动态解析舱门")

    # 简历上传组件
    uploaded_file = st.file_uploader(
        "请上传求职者真实 PDF 简历（限 5MB）：",
        type=["pdf"],
        help="上传后后端将利用 pypdf 引擎进行二进制文本抽干，并作为 System 控制链注入对话最顶端"
    )

    if uploaded_file is not None:
        # 加个简单的按钮防止重复提交
        if st.button("🚀 点击同步注入后端 AI 大脑", use_container_width=True):
            with st.spinner("📥 简历正在跨进程进行多维向量解析并写入落盘记忆..."):
                try:
                    # 将前端的文件打包成标准二进制流，POST 给后端简历解析网关
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    res = requests.post(
                        f"{BACKEND_BASE_URL}/upload_resume",
                        params={"session_id": session_option},
                        files=files
                    )
                    result_json = res.json()
                    if result_json.get("status") == "success":
                        st.success(f"✅ {result_json.get('message')}")
                    else:
                        st.error(f"❌ {result_json.get('message')}")
                except Exception as e:
                    st.error(f"💥 简历网关失联，详情: {str(e)}")

    st.markdown("---")
    st.info(
        f"💡 **当前沙盒密钥**: `{session_option}`\n\n"
        "后端正在运行全异步（Async）协程。由于开启了热重载（Auto Reload），"
        "现在修改后端逻辑不需要手动重启，代码将秒级自动对齐刷新！"
    )

# =====================================================================
# 3. 主聊天视窗 - 打字机、动态加载灯双剑合璧
# =====================================================================
st.title("🤖 大厂级 AI 技术初筛面试官")
st.caption("⚡ 基于 FastAPI 高性能异步长连接 | 动态 XML 标签攻防金钟罩 | Pydantic 结构化报告闭环")

# 渲染当前沙盒的前端历史对话记录
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 接收用户的核心输入
if user_query := st.chat_input("请输入您对面试官的回答..."):

    # A. 立即把用户的提问渲染到网页上，消灭视觉卡顿
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.chat_history.append({"role": "user", "content": user_query})

    # B. 🚨 核心加装：大模型思考加载灯与流式打字机闭环
    with st.chat_message("assistant"):
        # 💡 完美防假死：在大模型进行后台 RAG 检索、或者闭卷硬核生成报告期间，转圈提示闪亮登场
        with st.spinner("🧠 资深技术面试官正在复盘全量上下文、调取本地知识库深思中..."):
            try:
                # 开启 stream=True 长连接碎字泵水模式，限时充值到 60 秒
                response = requests.get(
                    f"{BACKEND_BASE_URL}/ask",
                    params={"question": user_query, "session_id": session_option},
                    stream=True,
                    timeout=60
                )


                # 声明一个极其平滑的流式碎片迭代发生器
                def chunk_generator():
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            yield chunk


                # 💡 极其丝滑：当 st.write_stream 拿到后端的第一个碎字时，上面的 spinner 加载圈会自动体面隐退，由打字机无缝接管输出！
                full_response = st.write_stream(chunk_generator())

            except Exception as e:
                st.error(f"💥 连线中断，详情: {str(e)}")
                full_response = "💥 核心网络网关遭受突发断流故障，请检查后端服务状态。"

        # C. 彻底吐完之后，将最终全量的 AI 回复锁进前端会话历史，用于维持状态
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})