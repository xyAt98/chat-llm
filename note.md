https://docs.ragas.io/en/stable/getstarted/evals

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

4. 在内存中构建一个 向量数据库 ， WEAVIATE_DOCS_INDEX_NAME 这是啥？？？ 索引的名字（有点类似于根据索引的名字区隔开不同的知识库）

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





# 可深入的点
1. 在整个应用程序的生命周期中初始化一次 向量数据库的连接  client（用的连接方法是 weaviate 提供的包）
2. 同时维护多个知识库连接， 用的是 langchain 实现的 Weaviate 高级抽象 

 1. 单例连接管理 (database.py):
    - WeaviateConnection 类确保整个应用只有一个数据库连接
    - get_vectorstore() 工厂函数支持多索引创建
  2. 动态索引支持 (chain.py):
    - ChatRequest 添加 index_name 参数，默认为 "wang_death_book"
    - get_retriever() 和 get_answer_chain() 支持动态索引选择
  3. 统一连接管理 (main.py, ingest.py):
    - 所有地方都使用单例连接，避免重复创建
    - 支持多知识库的灵活查询和存储
  
3. 动态 answer_chain 是怎么实现的？
在 app 生成的时候，app_routes 里传入的 Runnable 是一个继承了 Runnable 的一个对象， 里面有一个属性是 chain， 有一个 set_chain 的方法。初始 chain 为 None， 直到要使用 chain 的时候再构建 new_chain 并将 new_chain 赋值给 chain