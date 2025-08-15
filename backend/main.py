"""Main entrypoint for the app."""
from ast import Dict
import asyncio
from operator import index
from tokenize import String
from typing import Optional, Union
from uuid import UUID

from langchain_deepseek import ChatDeepSeek
import langsmith
from regex import P
from sklearn.calibration import StrOptions
from vector_store_manage import VectorStoreManager
from chain import ChatRequest, CollectionNotFoundError, get_answer_chain
# from chain import answer_chain
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from constants import WEAVIATE_DOCS_INDEX_NAME
from langserve import add_routes
from langsmith import Client
from pydantic import BaseModel
from dynamic_chain import dynamic_chain
from dynamic_chain import dynamic_chain

# 响应码常量定义
class ResponseCode:
    SUCCESS = 200
    BAD_REQUEST = 400
    INTERNAL_ERROR = 500

client = Client()
vector_store_manager = VectorStoreManager()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Dynamic chain selection based on index_name
# def get_chain_with_index(request: ChatRequest):
#     """Get chain with specified index name."""
#     return get_answer_chain(request.index_name or "wang_death_book")


add_routes(
    app,
    # answer_chain,
    dynamic_chain,
    path="/chat",
    input_type=ChatRequest,
    config_keys=["metadata", "configurable", "tags"],
)


class SendFeedbackBody(BaseModel):
    run_id: UUID
    key: str = "user_score"

    score: Union[float, int, bool, None] = None
    feedback_id: Optional[UUID] = None
    comment: Optional[str] = None


@app.post("/feedback")
async def send_feedback(body: SendFeedbackBody):
    client.create_feedback(
        body.run_id,
        body.key,
        score=body.score,
        comment=body.comment,
        feedback_id=body.feedback_id,
    )
    return {"result": "posted feedback successfully", "code": ResponseCode.SUCCESS}


class UpdateFeedbackBody(BaseModel):
    feedback_id: UUID
    score: Union[float, int, bool, None] = None
    comment: Optional[str] = None


@app.patch("/feedback")
async def update_feedback(body: UpdateFeedbackBody):
    feedback_id = body.feedback_id
    if feedback_id is None:
        return {
            "result": "No feedback ID provided",
            "code": ResponseCode.BAD_REQUEST,
        }
    client.update_feedback(
        feedback_id,
        score=body.score,
        comment=body.comment,
    )
    return {"result": "patched feedback successfully", "code": ResponseCode.SUCCESS}


# TODO: Update when async API is available
async def _arun(func, *args, **kwargs):
    return await asyncio.get_running_loop().run_in_executor(None, func, *args, **kwargs)


async def aget_trace_url(run_id: str) -> str:
    for i in range(5):
        try:
            await _arun(client.read_run, run_id)
            break
        except langsmith.utils.LangSmithError:
            await asyncio.sleep(1**i)

    if await _arun(client.run_is_shared, run_id):
        return await _arun(client.read_run_shared_link, run_id)
    return await _arun(client.share_run, run_id)


class GetTraceBody(BaseModel):
    run_id: UUID


@app.post("/get_trace")
async def get_trace(body: GetTraceBody):
    run_id = body.run_id
    if run_id is None:
        return {
            "result": "No LangSmith run ID provided",
            "code": ResponseCode.BAD_REQUEST,
        }
    return await aget_trace_url(str(run_id))


@app.post("/knowledge/book")
async def get_knowledge_from_book(body: str):
    """处理知识库中数据源(形式为本地文档)的上传"""
    return None


class FetchUrlBody(BaseModel):
    url: str


@app.post("/knowledge/url")
async def get_knowledge_from_url(body: FetchUrlBody):
    from chain import get_answer_chain

    from chain import get_answer_chain

    url = body.url
    """处理知识库中数据源(形式为URL)的上传"""
    if not is_valid_url(url):
        return {"error": "Invalid URL format", "code": ResponseCode.BAD_REQUEST}
    
    try:
        docs = load_url_content(url)
        if not docs:
            return {"error": "Failed to load content from URL", "code": ResponseCode.BAD_REQUEST}
        
        # 3. 生成标题
        title = extract_title_from_docs(docs)

        # 4. 根据title生成index name
        index_name = generate_index_name(url, title)
        
        # 5. 嵌入内容并存入数据库
        embed_and_store_content(docs, index_name)
        
        # 6. 生成示例问题
        example_questions = generate_example_questions(docs)

        # 7. 根据 index name 构建 answer chain
        chain = get_answer_chain(index_name)
        dynamic_chain.set_chain(chain)

        return {"title": title, "index_name": index_name, "code": ResponseCode.SUCCESS, "example_questions": example_questions}
        
    except Exception as e:
        return {"error": f"Failed to process URL: {str(e)}", "code": ResponseCode.INTERNAL_ERROR}


def is_valid_url(url: str) -> bool:
    """验证URL格式是否合格"""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def load_url_content(url: str):
    """加载URL内容"""
    from langchain.document_loaders import WebBaseLoader
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        return docs
    except Exception as e:
        print(f"Error loading URL content: {e}")
        return None


def generate_index_name(url: str, title: str) -> str:
    """根据title生成index name，在title后加index_name并符合命名规范"""
    import re
    from urllib.parse import urlparse
    
    # 清理title，转换为适合作为index name的格式
    clean_title = title.lower()
    clean_title = re.sub(r'[^a-z0-9\s]', '', clean_title)  # 移除非字母数字字符
    clean_title = re.sub(r'\s+', '_', clean_title)  # 空格替换为下划线
    clean_title = clean_title.strip('_')
    
    # 清理title，转换为适合作为index name的格式
    clean_title = title.lower()
    clean_title = re.sub(r'[^a-z0-9\s]', '', clean_title)  # 移除非字母数字字符
    clean_title = re.sub(r'\s+', '_', clean_title)  # 空格替换为下划线
    clean_title = clean_title.strip('_')
    
    # 生成index name
    index_name = f"{clean_title}_index_name"
    # 生成index name
    index_name = f"{clean_title}_index_name"
    
    # 确保index name符合Weaviate命名规范
    index_name = re.sub(r'[^a-z0-9_]', '_', index_name)  # 再次确保只包含允许的字符
    index_name = re.sub(r'_+', '_', index_name)  # 合并多个下划线
    index_name = index_name.strip('_')  # 移除首尾下划线
    index_name = re.sub(r'[^a-z0-9_]', '_', index_name)  # 再次确保只包含允许的字符
    index_name = re.sub(r'_+', '_', index_name)  # 合并多个下划线
    index_name = index_name.strip('_')  # 移除首尾下划线
    
    # 限制长度
    # 限制长度
    return index_name[:50]  # 限制长度


def embed_and_store_content(docs, index_name: str):
    """将内容嵌入并存入数据库"""
    # 使用现有的embedding模型和数据库连接
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    # from backend.vector_database import get_vectorstore
    import os
    
    # 分割文档
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
    docs_transformed = text_splitter.split_documents(docs)
    
    # 确保metadata包含必要字段
    for doc in docs_transformed:
        if "source" not in doc.metadata:
            doc.metadata["source"] = ""
        if "title" not in doc.metadata:
            doc.metadata["title"] = ""
    
    # 使用单例连接创建vector store
    vectorstore = vector_store_manager.get_vector_store_client(index_name)
    # vectorstore = get_vectorstore(index_name)
    
    # 使用record manager进行去重
    from langchain.indexes import SQLRecordManager, index
    record_manager = SQLRecordManager(
        f"weaviate/{index_name}",
        db_url=os.environ["RECORD_MANAGER_DB_URL"],
    )
    record_manager.create_schema() # 这是在干嘛？ 每次都得这样吗？
    
    # 索引文档
    indexing_stats = index(
        docs_transformed,
        record_manager,
        vectorstore,
        batch_size=64,
        cleanup="full",
        source_id_key="source",
    )
    # TODO: 这里考虑将 index 记录写入 log

    return indexing_stats

def generate_example_questions(docs):
    """基于刚加入的知识生成4个示例问题"""
    # TODO： 考虑 RAPTOR 优化这个过程
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    # 处理长文本问题：只取前几段作为上下文
    content = docs[0].page_content if docs else ""
    
    # 如果内容太长，截取前2000个字符
    if len(content) > 2000:
        content = content[:2000] + "..."
    
    prompt_template = """
        基于以下内容，生成4个有意义的示例问题。这些问题应该能够帮助用户更好地理解和利用这些知识。

        要求：
        1. 问题要具体、明确
        2. 问题要覆盖内容的主要要点
        3. 问题要有实际意义和价值
        4. 每个问题占一行

        内容：
        {content}

        请生成4个示例问题（每行一个问题）：
        """
    
    llm = ChatDeepSeek(model="deepseek-chat", temperature=0.7)
    prompt = PromptTemplate.from_template(prompt_template)
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        questions_text = chain.invoke({'content': content})
        
        # 将文本按行分割，去除空行
        questions = [q.strip() for q in questions_text.strip().split('\n') if q.strip()]
        
        # 确保只返回4个问题
        return questions[:4]
        
    except Exception as e:
        print(f"Error generating example questions: {e}")
        return []

def extract_title_from_docs(docs) -> str:
    # """使用大模型基于文档内容生成合适的标题"""
    # if not docs or len(docs) == 0:
    #     return "Untitled"
    
    # # 如果内容太长，截取前3000个字符作为上下文
    # content = docs[0].page_content if docs else ""
    # if len(content) > 3000:
    #     content = content[:3000] + "..."
    
    # prompt_template = """
    #     基于以下内容，生成一个简洁、准确、有意义的标题。
        
    #     要求：
    #     1. 标题要能准确反映内容的主题
    #     2. 标题要简洁明了，最好在10个字以内
    #     3. 避免使用过于笼统的词汇
    #     4. 如果内容来自特定领域，标题应该体现该领域特征
        
    #     内容：
    #     {content}
        
    #     请生成一个合适的标题：
    #     """
    
    # llm = ChatDeepSeek(model="deepseek-chat", temperature=0.3)
    # from langchain_core.prompts import PromptTemplate
    # from langchain_core.output_parsers import StrOutputParser
    
    # prompt = PromptTemplate.from_template(prompt_template)
    # chain = prompt | llm | StrOutputParser()
    
    # try:
    #     generated_title = chain.invoke({'content': content}).strip()
        
    #     # 清理生成的标题，去除多余的引号和换行符
    #     generated_title = generated_title.replace('"', '').replace('\n', '').strip()
        
    #     # 如果生成的标题为空或太短，使用备用方案
    #     if len(generated_title) < 2:
    #         # 尝试从metadata中获取title
    #         title = docs[0].metadata.get("title", "")
    #         if title:
    #             return title
            
    #         # 如果没有title，尝试从URL中提取
    #         if docs[0].metadata.get("source"):
    #             from urllib.parse import urlparse
    #             parsed = urlparse(docs[0].metadata["source"])
    #             return parsed.netloc
            
    #         return "Untitled"
        
    #     return generated_title
        
    # except Exception as e:
    #     print(f"Error generating title with LLM: {e}")
    # 备用方案：使用原有的简单提取方法
    title = docs[0].metadata.get("title", "")
    if title:
        return title
    
    if docs[0].metadata.get("source"):
        from urllib.parse import urlparse
        parsed = urlparse(docs[0].metadata["source"])
        return parsed.netloc
    
    return "Untitled"

def get_sources_by_index_name(index_name):
    client = vector_store_manager.get_client()
    if client:
        res = client.query.aggregate(index_name)\
            .with_group_by_filter(["source"])\
            .with_fields("groupedBy { value } ")\
            .do()
        sources = []
        for group in res["data"]["Aggregate"][index_name]:
            sources.append(group["groupedBy"]["value"])
        return sources

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/check_vector_store/{index_name}")
def check_vector_store_and_get_sources(index_name: str):
    try:
        chain = get_answer_chain(index_name)
        dynamic_chain.set_chain(chain)
        sources = get_sources_by_index_name(index_name)
    except CollectionNotFoundError as e:
        return {"error": str(e), "code": ResponseCode.BAD_REQUEST} 
    return {"message": "success", "code": ResponseCode.SUCCESS, "data": {"sources": sources}}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
