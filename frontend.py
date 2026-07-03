import streamlit as st
import requests

# 1. 网页基础排版配置
st.set_page_config(page_title="AI 智能技术初筛战舰", layout="wide")
st.title("🚀 大厂级 AI 技术初筛与全自动多轮面试系统")

BACKEND_URL = "http://127.0.0.1:8005/api/v1"

# --- 2. 侧边栏：配置候选人身份与简历灌入 ---
with st.sidebar:
    st.header("👤 候选人管理中心")
    candidate_id = st.text_input("候选人唯一 ID", value="candidate_zhangsan_007")

    st.divider()
    st.header("📄 简历特征原始数据灌入")
    resume_text = st.text_area("请贴入候选人的原始简历文本", height=180,
                               value="张三，精通 Python 后端研发。在项目中使用 FastAPI 纯异步协程架构重构了核心路由，引入 StreamingResponse 实现了大模型碎字流式吐出。")

    if st.button("🚀 强行灌入向量冷仓", use_container_width=True):
        if not resume_text.strip():
            st.error("简历内容不能为空！")
        else:
            with st.spinner("正在通过智谱 Embedding-3 向量化并物理落盘..."):
                try:
                    res = requests.post(f"{BACKEND_URL}/rag/ingest", json={
                        "candidate_id": candidate_id,
                        "raw_text": resume_text
                    })
                    if res.status_code == 200:
                        st.success("🎉 真实线上高精向量库灌入成功！")
                    else:
                        st.error(f"灌入失败: {res.text}")
                except Exception as e:
                    st.error(f"连接后端暴雷: {str(e)}")

    st.divider()
    # 📌 核心加码功能一：一键清空当前网页缓存，方便开启下一场面试
    if st.button("🔄 清空当前网页对话", type="secondary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 3. 主界面：多轮流式碎字聊天对线舱 ---
st.header("💬 工业级流式技术对线沙盒")

# 初始化 Streamlit 本地网页聊天历史缓存
if "messages" not in st.session_state:
    st.session_state.messages = []

# 渲染现有的聊天对话流
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入对话框
if user_query := st.chat_input("以候选人的身份回答面试官的问题..."):
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    # 渲染大模型面试官的流式喷字打字机
    with st.chat_message("assistant"):
        placeholder = st.empty()  # 初始化打字机画布
        full_response = ""

        try:
            # 向后端 8005 端口发起流式长连接请求
            with requests.post(
                    f"{BACKEND_URL}/chat/completions",
                    json={"candidate_id": candidate_id, "user_query": user_query},
                    stream=True  # 开启核心流式传输开关
            ) as r:
                for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        full_response += chunk
                        placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)  # 吐字完毕，去掉光标

            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"流式通道断裂: {str(e)}")

st.divider()

# --- 4. 底部业务闭环：一键评审大报告 + 前端下载本地化 ---
st.header("📊 终结面试：大厂首席架构师定级评估报告")
if st.button("🎯 触发多轮记忆审计，一键生成评审大报告", type="primary"):
    with st.spinner("首席架构师正在全量翻阅历史老账本并撰写报告..."):
        try:
            res = requests.post(f"{BACKEND_URL}/interview/report?candidate_id={candidate_id}")
            if res.status_code == 200:
                report_data = res.json()
                raw_markdown_report = report_data.get("evaluation_report")

                st.success(f"💾 后端物理落盘成功！存储路径: {report_data.get('saved_at')}")

                # 渲染 Markdown 内容到网页上
                st.markdown(raw_markdown_report)

                # 📌 核心加码功能二：把生成的 Markdown 报告转化为前端可直接下载的字节流
                st.download_button(
                    label="📥 点击将这份大厂评审报告下载到本地 (.md)",
                    data=raw_markdown_report,
                    file_name=f"技术定级报告_{candidate_id}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            else:
                st.error(f"生成报告失败: {res.json().get('detail')}")
        except Exception as e:
            st.error(f"评审网关暴雷: {str(e)}")