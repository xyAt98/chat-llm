
# 组件
weaviate 向量数据库好像是
supabase postgres 的云数据库（目前没看到用在哪里了）


# 后端

后端结构很简单， 一个 main.py 控制主流程， ingest.py 脚本将数据读入向量数据库， chain.py 包含定义 llm 和 receiver

需要额外关注的核心： 数据库、 chain、 数据流

## ingest

简述一下流程：

1. spliter 用的是 langchain 的 `from langchain.text_splitter import RecursiveCharacterTextSplitter`
这里应该是有优化的空间的

2. 词嵌入， 直接用的 ZhipuAI

3. 连接上 weaviate 云向量数据库客户端

4. 在内存中构建一个 向量数据库 ， WEAVIATE_DOCS_INDEX_NAME 这是啥？？？

5. record_manager ？ postgres 的数据库？ 用处是啥？

6. 对数据构建索引

# 前端

/frontend/app/page.tsx#L13  
`<ChatWindow conversationId={uuidv4()}></ChatWindow>`
由 uuidv4() 生成 conversationId , 传给后端并在对话期间一直使用这个 id 进行对话。
每次页面刷新或重新加载时，都会生成一个新的 conversationId


# debug
调用 stream_log ， 可以在 langsmith 平台上看每一个 chain 实例有没有什么问题。 没有任何问题

前端调用


# 问题
流式输出（SSE）+ 异步迭代: frontend/app/components/ChatWindow.tsx: 136


# 评估

有正确答案的 和 没有正确答案的 都能进行评估。（answer correctness ）

我侧重于一个什么呢？

我要用什么数据集呢？

难道我不在一家公司， 我就没办法做一个项目了吗？




