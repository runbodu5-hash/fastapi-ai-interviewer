import os
from dotenv import load_dotenv

load_dotenv()

import json
import uuid
import re
from typing import List, AsyncGenerator
from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# --- 1. LANGCHAIN 核心组件引入 ---
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.stores import InMemoryStore
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import aiofiles
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


# --- 2. WAF 安全前置网关 ---
class ContentSecurityWAF:
    @staticmethod
    def sanitize_input(text: str) -> str:
        if not text: return ""
        dangerous_patterns = r'</?(user_query|system_instruction|system|assistant|human|prompt|instruction)>'
        clean_text = re.sub(dangerous_patterns, '', text, flags=re.IGNORECASE)
        return clean_text.strip()


# --- 3. 依据 .env 变量名像素级对齐真实算力 ---
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
MODEL_NAME = os.getenv("DEEPSEEK_MODEL", "glm-4-flash")

# --- 4. 核心引擎配置 ---
embedding_engine = OpenAIEmbeddings(
    openai_api_key=API_KEY,
    openai_api_base=BASE_URL,
    model="embedding-3"
)

llm_engine = ChatOpenAI(
    openai_api_key=API_KEY,
    openai_api_base=BASE_URL,
    model=MODEL_NAME,
    streaming=True
)

# --- 5. 初始化 FastAPI 容器与物理仓 ---
app = FastAPI(title="核心项目全功能闭环系统")

HISTORY_DIR = os.path.join(os.path.dirname(__file__), "history")
os.makedirs(HISTORY_DIR, exist_ok=True)

vector_db = Chroma(collection_name="industrial_safe_vault", embedding_function=embedding_engine)
parent_kv_store = InMemoryStore()

parent_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=60)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=120, chunk_overlap=15)


class ResumeIngestPayload(BaseModel):
    candidate_id: str
    raw_text: str


class ChatPayload(BaseModel):
    candidate_id: str
    user_query: str


class AsyncHistoryManager:
    @staticmethod
    def _get_file_path(candidate_id: str) -> str:
        return os.path.join(HISTORY_DIR, f"history_{candidate_id}.json")

    @classmethod
    async def load_memory_as_langchain_messages(cls, candidate_id: str) -> List:
        file_path = cls._get_file_path(candidate_id)
        if not os.path.exists(file_path): return []
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
            if not content.strip(): return []
            raw_list = json.loads(content)
            messages = []
            for round_data in raw_list:
                if round_data["role"] == "user":
                    messages.append(HumanMessage(content=round_data["content"]))
                elif round_data["role"] == "assistant":
                    messages.append(AIMessage(content=round_data["content"]))
            return messages

    @classmethod
    async def save_round(cls, candidate_id: str, role: str, content: str):
        file_path = cls._get_file_path(candidate_id)
        history = []
        if os.path.exists(file_path):
            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                txt = await f.read()
                if txt.strip(): history = json.loads(txt)
        history.append({"role": role, "content": content})
        async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(history, ensure_ascii=False, indent=2))


# --- 6. 核心业务路由层 ---
main_router = APIRouter(prefix="/api/v1", tags=["智能体核心安全引擎"])


@main_router.post("/rag/ingest", summary="简历真实线上高精灌入网关")
async def ingest_resume_gateway(payload: ResumeIngestPayload):
    safe_text = ContentSecurityWAF.sanitize_input(payload.raw_text)
    if not safe_text: raise HTTPException(status_code=400, detail="输入的简历文本不能为空")

    master_doc = Document(page_content=safe_text, metadata={"candidate_id": payload.candidate_id})
    segmented_parents = parent_splitter.split_documents([master_doc])
    total_child_inserted = 0

    for parent_chunk in segmented_parents:
        parent_uuid = str(uuid.uuid4())
        micro_children = child_splitter.split_documents([parent_chunk])
        for child in micro_children:
            child.metadata["doc_id"] = parent_uuid
            child.metadata["candidate_id"] = payload.candidate_id
        vector_db.add_documents(micro_children)
        parent_kv_store.mset([(parent_uuid, parent_chunk)])
        total_child_inserted += len(micro_children)

    return {"status": "success", "processed_parents": len(segmented_parents), "indexed_children": total_child_inserted}


@main_router.post("/chat/completions", summary="带WAF前置防线的流式长连接响应网关")
async def chat_completions_gateway(payload: ChatPayload):
    safe_query = ContentSecurityWAF.sanitize_input(payload.user_query)
    if not safe_query: raise HTTPException(status_code=400, detail="提问内容经过合规洗涤后结构为空")

    chat_history = await AsyncHistoryManager.load_memory_as_langchain_messages(payload.candidate_id)

    enforced_kwargs = {"filter": {"candidate_id": payload.candidate_id}, "k": 1}
    matched_children = vector_db.similarity_search(safe_query, **enforced_kwargs)

    context_corpus = "未检索到相关简历背景"
    if matched_children:
        parent_uuids = [child.metadata.get("doc_id") for child in matched_children if child.metadata.get("doc_id")]
        final_parent_docs = parent_kv_store.mget(parent_uuids)
        if final_parent_docs and final_parent_docs[0]:
            context_corpus = final_parent_docs[0].page_content

    await AsyncHistoryManager.save_round(payload.candidate_id, "user", safe_query)

    system_prompt = SystemMessage(content=(
        "你是一个大厂的硬核技术面试官。请基于以下提供的候选人简历上下文背景，"
        "结合与候选人的历史对话记录，针对他提到的技术栈进行犀利、深度的连连追问。\n"
        f"【候选人当前简历局部上下文】:\n{context_corpus}"
    ))

    full_messages = [system_prompt] + chat_history + [HumanMessage(content=safe_query)]

    async def text_stream_generator() -> AsyncGenerator[str, None]:
        full_reply_accumulator = []
        try:
            async for chunk in llm_engine.astream(full_messages):
                token = chunk.content
                if token:
                    full_reply_accumulator.append(token)
                    yield token

            complete_ai_response = "".join(full_reply_accumulator)
            await AsyncHistoryManager.save_round(payload.candidate_id, "assistant", complete_ai_response)
        except Exception as e:
            yield f"\n\n[🚨 线上流式通道高危拦截] 异常内幕: {str(e)}\n"

    # 📌 核心修复卡位：显式指定 charset=utf-8，从后端直接扼杀前端网页的解码乱容！
    return StreamingResponse(text_stream_generator(), media_type="text-event-stream; charset=utf-8")


@main_router.post("/interview/report", summary="一键生成并物理落盘候选人技术定级大报告")
async def generate_interview_report(candidate_id: str = Query(..., description="候选人唯一ID")):
    file_path = AsyncHistoryManager._get_file_path(candidate_id)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="未找到该候选人的面试多轮对话记录，无法生成报告")

    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
        content = await f.read()
        if not content.strip() or content.strip() == "[]":
            raise HTTPException(status_code=400, detail="面试记录为空，请至少进行一轮技术对线")

    review_prompt = [
        SystemMessage(content=(
            "你是一家大厂的首席架构师兼技术总面试官。请仔细阅读以下技术初筛的多轮对话历史记录，"
            "结合候选人的简历背景，客观、严谨地从技术深度、实际踩坑经验、最终定级与建议三个维度，"
            "生成一份评估报告。请直接输出纯 Markdown 格式的专业报告，不要包含任何客套话。"
        )),
        HumanMessage(content=f"以下是候选人（ID: {candidate_id}）的完整面试对话账本：\n\n{content}")
    ]

    try:
        evaluation_result = await llm_engine.ainvoke(review_prompt)
        report_markdown = evaluation_result.content

        REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")
        os.makedirs(REPORT_DIR, exist_ok=True)

        target_report_path = os.path.join(REPORT_DIR, f"report_{candidate_id}.md")
        async with aiofiles.open(target_report_path, mode='w', encoding='utf-8') as pf:
            await pf.write(report_markdown)

        return {
            "status": "success",
            "candidate_id": candidate_id,
            "saved_at": target_report_path,
            "evaluation_report": report_markdown
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"大模型评审网关暴雷: {str(e)}")


app.include_router(main_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8005, reload=True)