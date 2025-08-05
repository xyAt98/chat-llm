# 后端

后端结构很简单， 一个 main.py 控制主流程， ingest.py 脚本将数据读入向量数据库， chain.py 包含定义 llm 和 receiver

需要额外关注的核心： 数据库、 chain、 数据流

# 前端



# 组件
weaviate 向量数据库好像是
supabase postgres 的云数据库

# debug
调用 stream_log ， 可以在 langsmith 平台上看每一个 chain 实例有没有什么问题。 没有任何问题

前端调用


# 问题
流式输出（SSE）+ 异步迭代: frontend/app/components/ChatWindow.tsx: 136

