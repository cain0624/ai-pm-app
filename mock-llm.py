#!/usr/bin/env python3
"""Mock OpenAI 兼容服务：离线演示/测试 AI 教练的 agent 循环。

用法：python3 mock-llm.py   （监听 127.0.0.1:8124）
app 设置里填 base=http://localhost:8124/v1，模型名随意，key 随意。

脚本化行为：
- 用户消息 → 调 get_progress
- get_progress 结果 → 说一句话 + 调 run_quiz（两道题，参数分片流式下发，验证拼装）
- run_quiz 结果 → 总结性回复
- 非流式请求（测试连接）→ pong
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

QUIZ_ARGS = json.dumps({"questions": [
    {"q": "RAG 的核心作用是？",
     "opts": ["先检索知识库再生成，答案可溯源", "加密数据传输", "压缩存储成本", "加速数据库索引"],
     "ans": 0, "exp": "RAG 让模型回答前先检索企业知识库，是控制幻觉的第一层防护。",
     "topic": "AI客服 · 幻觉治理"},
    {"q": "containment rate 指什么？",
     "opts": ["系统并发承载能力", "AI 独立解决率（不转人工）", "用户留存率", "上下文保持能力"],
     "ans": 1, "exp": "AI 不转人工独立完成会话的占比，需与 CSAT/FCR 联看。",
     "topic": "AI客服 · 人机协同"},
]}, ensure_ascii=False)


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            body = {}
        msgs = body.get("messages", [])
        last = msgs[-1] if msgs else {}
        sys_text = " ".join(str(m.get("content", "")) for m in msgs if m.get("role") == "system")

        if not body.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps(
                {"choices": [{"message": {"role": "assistant", "content": "pong"}}]}).encode())
            return

        if "模拟面试官" in sys_text:
            # ---- 模拟面试脚本 ----
            if last.get("role") == "user":
                q1 = json.dumps({"question": "Q1：项目里整体 containment 71%，但长尾纠纷场景掉到 40% 以下，你会怎么归因并设计改进方案？", "topic": "AI客服 · 人机协同"}, ensure_ascii=False)
                chunks = [{"content": "你好，我是本场面试官。材料我已看完，我们直接开始。"},
                          {"tool_calls": [{"index": 0, "id": "iv1", "type": "function",
                                           "function": {"name": "ask_question", "arguments": q1}}]}]
            elif last.get("role") == "tool" and last.get("name") == "ask_question":
                n = sum(1 for m in msgs if m.get("role") == "tool" and m.get("name") == "ask_question")
                if n >= 10:
                    fin = json.dumps({"overall": 78,
                                      "dims": [{"name": "产品思维", "score": 85, "comment": "能锚定指标归因"},
                                               {"name": "技术理解", "score": 75, "comment": "架构基本清楚"},
                                               {"name": "结构化表达", "score": 82, "comment": "分点清晰"},
                                               {"name": "落地经验", "score": 70, "comment": "案例偏少"}],
                                      "summary": "整体表现良好：能从指标出发定位问题并给出分层方案；建议加强对合规细节与商业化权衡的展开。",
                                      "perQ": ["Q1 归因清晰", "Q2 方案分层", "Q3 指标意识好", "Q4 权衡明确", "Q5 略浅",
                                               "Q6 结构好", "Q7 有数据感", "Q8 漏了留痕期限", "Q9 定价逻辑顺", "Q10 反问加分"]},
                                     ensure_ascii=False)
                    chunks = [{"tool_calls": [{"index": 0, "id": "ivf", "type": "function",
                                               "function": {"name": "finish_interview", "arguments": fin}}]}]
                else:
                    txt = "收到，思路清楚。"
                    q = json.dumps({"question": f"Q{n+1}：追问第 {n+1} 题——商户知识库上线平均 9 天，你会怎么设计把它压到 3 天以内的产品方案？", "topic": "ToB 交付"}, ensure_ascii=False)
                    chunks = [{"content": txt},
                              {"tool_calls": [{"index": 0, "id": f"iv{n+1}", "type": "function",
                                               "function": {"name": "ask_question", "arguments": q}}]}]
            elif last.get("role") == "tool" and last.get("name") == "finish_interview":
                chunks = [{"content": "本场模拟面试结束，评估卡已生成，可收藏回顾。"}]
            else:
                chunks = [{"content": "请继续。"}]
            self.sse(chunks)
            return

        if last.get("role") == "user":
            user_text = last.get("content", "")
            if "标记" in user_text or "掌握" in user_text:
                chunks = [
                    {"tool_calls": [{"index": 0, "id": "call_3", "type": "function",
                                     "function": {"name": "mark_mastered",
                                                  "arguments": json.dumps({"topic": "幻觉治理"}, ensure_ascii=False)}}]},
                ]
            else:
                chunks = [
                    {"role": "assistant", "content": ""},
                    {"tool_calls": [{"index": 0, "id": "call_1", "type": "function",
                                     "function": {"name": "get_progress", "arguments": ""}}]},
                ]
        elif last.get("role") == "tool" and last.get("name") == "get_progress":
            chunks = [
                {"content": "看过你的错题本了，出两题验证一下掌握度。"},
                {"tool_calls": [{"index": 0, "id": "call_2", "type": "function",
                                 "function": {"name": "run_quiz", "arguments": QUIZ_ARGS[:60]}}]},
                {"tool_calls": [{"index": 0,
                                 "function": {"arguments": QUIZ_ARGS[60:]}}]},
            ]
        elif last.get("role") == "tool" and last.get("name") == "mark_mastered":
            try:
                res = json.loads(last.get("content") or "{}")
                txt = ("✅ 已把「%s」标记为已掌握，首页的🔖标记里能看到。" % res.get("markedTopic", "")) \
                    if res.get("ok") else ("标记失败：%s" % res.get("reason", ""))
            except Exception:
                txt = "标记操作已执行。"
            mid = len(txt) // 2
            chunks = [{"content": txt[:mid]}, {"content": txt[mid:]}]
        elif last.get("role") == "tool" and last.get("name") == "run_quiz":
            try:
                res = json.loads(last.get("content") or "{}")
                txt = ("得分 %s/%s。" % (res.get("score"), res.get("total"))
                       + " 答错的题重点看解析：幻觉防护要靠多层金字塔，不是单点。"
                         "掌握得差不多了，我把这个主题标记一下？")
            except Exception:
                txt = "收到你的作答结果。"
            mid = len(txt) // 2
            chunks = [{"content": txt[:mid]}, {"content": txt[mid:]}]
        else:
            chunks = [{"content": "收到。"}]
        self.sse(chunks)

    def sse(self, chunks):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self._cors()
        self.end_headers()
        for c in chunks:
            self.wfile.write(b"data: " + json.dumps(
                {"choices": [{"delta": c}]}, ensure_ascii=False).encode() + b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("mock LLM on http://127.0.0.1:8124/v1")
    HTTPServer(("127.0.0.1", 8124), Handler).serve_forever()
