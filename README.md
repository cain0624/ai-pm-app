# AI 产品经理刷题 · AI 面试教练

一个单文件移动端风格的 AI 产品经理学习应用。

## 功能
- **首页**：50 道 AI PM 面试题（TikTok 式上下滑 + 语音朗读），收藏 / 标记 / 过滤
- **播客**：5 期 AI 播客图文拆解（含源音频播放）
- **刷题**：50 道选择题，错题本 + 只刷错题，可收藏
- **教练**：带工具调用循环的 AI 面试教练（真正的 agent）——读你的错题本/收藏、出交互式测验、看结果再讲解；还有「随机抽查」10 题闭环

## 使用
- 直接打开 `index.html`，或访问 GitHub Pages 部署地址
- 教练 Tab 需在「设置」填一个 OpenAI 兼容 API。默认已预填硅基流动 `https://api.siliconflow.cn/v1` + `deepseek-ai/DeepSeek-V4-Flash`（跨域与 function calling 均实测可用），**只差你自己填一把 key**
- 随机抽查与首页语音不需要 key

> ⚠️ 纯静态页由浏览器直连厂商，所以**厂商必须回跨域（CORS）头**，否则预检就会被浏览器拦掉——curl 能通不代表页面能用。已实测：硅基流动 ✅、DeepSeek ✅；未实测：智谱 / OpenRouter / Ollama。像 `api.devin-tec.cn` 这类中转站实测**不回** CORS 头，页面里用不了。

## 离线演示教练对话
```bash
python3 mock-llm.py   # 监听 127.0.0.1:8124
```
教练设置里填 `http://localhost:8124/v1`，模型名/key 随意。
