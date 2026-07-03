import requests

URL = "http://127.0.0.1:8999/ask"
params = {
    "question": "你们深圳的 Python 后端岗位有什么技术要求？",
    "session_id": "test_candidate_zhangsan"
}

print("🚀 发起终极脱水彻查...")
try:
    response = requests.get(URL, params=params, timeout=15)
    print(f"📡 后端 HTTP 状态码: {response.status_code}")
    print("\n================== 📡 后端原始返回 ==================")
    print(f"原始文本: {response.text}")

    # 彻底防炸：先判断是不是真的拿到了字典
    data = response.json()
    if isinstance(data, dict) and "answer" in data:
        print(f"\n👨‍💻 AI面试官答复: {data['answer']}")
    else:
        print(f"\n⚠️ 警告：后端给的数据结构不对！拿到的原始JSON是: {data}")
    print("==============================================================")
except Exception as e:
    print(f"💥 彻底故障: {str(e)}")