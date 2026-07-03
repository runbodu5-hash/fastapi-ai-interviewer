import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# =====================================================================
# 1. 基础环境确权（配置你的远程 Embedding 桥梁）
# =====================================================================
# 提示：即使使用 DeepSeek，LangChain 官方也推荐通过 OpenAI 类进行兼容性桥接
os.environ["OPENAI_API_KEY"] = "DEEPSEEK_API_KEY"
os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com/v1"  # 映射到官方网关 Base URL


def run_ingest():
    """
    离线数据灌入核心主函数
    """
    # 路径确权：定义我们数据源的路径，和最终数据库落地的文件夹位置
    raw_text_path = "data/job.txt"
    persist_db_dir = "./chroma_db"

    # =====================================================================
    # 2. 读取私有文档（Document Loading）
    # =====================================================================
    print(f"📂 [Step 1/4] 正在从本地磁盘读取原始文档: {raw_text_path} ...")
    if not os.path.exists(raw_text_path):
        print(f"❌ 错误：未在 {raw_text_path} 找到文本文件，请先创建它并塞入内容！")
        return

    loader = TextLoader(raw_text_path, encoding="utf-8")
    raw_documents = loader.load()
    print("✅ 原始文档加载成功。")

    # =====================================================================
    # 3. 语义文本切片（Document Chunking）
    # =====================================================================
    print("✂️ [Step 2/4] 启动黄金参数切片器...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,  # 每个豆腐块最多 300 个字，锁死语义边界
        chunk_overlap=50,  # 50字重叠区，防止核心技术词被拦腰切断
        length_function=len
    )
    splitted_chunks = text_splitter.split_documents(raw_documents)
    print(f"✅ 文本重组完毕，共产生 {len(splitted_chunks)} 个高密度语义豆腐块。")

    # =====================================================================
    # 4. 初始化同声传译引擎（Embedding Model Configuration）
    # =====================================================================
    print("🧬 [Step 3/4] 正在连接远程矩阵计算服务器...")
    # 注意：这里的模型名称需要替换为你所使用的服务商提供的专用 Embedding 模型标识符
    embedding_engine = OpenAIEmbeddings(model="text-embedding-3-small")

    # =====================================================================
    # 5. 计算坐标并强行落地（Vector Storage & Persistence）
    # =====================================================================
    print(f"💾 [Step 4/4] 正在向本地 ChromaDB 写入向量，物理路径: {persist_db_dir} ...")

    # 这一行代码会做三件事：
    # ① 把 splitted_chunks 顺着网线发给 Embedding 接口算成 1536 维坐标
    # ② 把算好的坐标跟文本块一一对齐绑定
    # ③ 在本地项目目录下强行生成一个名为 chroma_db 的物理文件夹，写入二进制文件
    vector_store = Chroma.from_documents(
        documents=splitted_chunks,
        embedding=embedding_engine,
        persist_directory=persist_db_dir
    )

    print("\n" + "=" * 50)
    print("🏁 核心资产确权成功！Chroma 向量数据库已成功固化到本地磁盘！")
    print("💡 你的项目目录下现在已经多出了一个 [chroma_db] 文件夹，数据预处理管道安全下机。")
    print("=" * 50)


if __name__ == "__main__":
    run_ingest()