"""Database connection management for Weaviate."""
import os
import weaviate

from typing import Optional
from langchain_community.vectorstores import Weaviate
from threading import Lock

from utils import get_embeddings_model


class VectorStoreManager:
    """Singleton class for managing Weaviate VectorStore."""
    _instance: Optional['VectorStoreManager'] = None
    _lock = Lock()
    _client = None # weaviate database client
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # create weaviate client， only one， 奇怪，这里又没锁， 为什么能实现 singleton weaviate client ?
        if hasattr(self, '_initialized'): # 这tm不是对象的属性吗, 这里为什么要判断啊， _new_不是已经保证单例了吗
            return
        if self._client is None:
            self._client = weaviate.Client(
                url=os.environ["WEAVIATE_URL"],
                auth_client_secret=weaviate.AuthApiKey(api_key=os.environ["WEAVIATE_API_KEY"]),
            )
        
        """{index_key: vector store instance}
        
        self._vector_stores["combined"] = Weaviate(
            client=self._client,
            index_name=os.environ["WEAVIATE_DOCS_INDEX_NAME"],
            text_key="text",
            embedding=OpenAIEmbeddings(chunk_size=200),
            by_text=False,
            attributes=["source", "title"],
        )
        """
        self._vector_stores = {}
        
        self._initialized = True

    def get_client(self):
        return self._client


    def get_vector_store_client(self, index_name: str):
        # 当 index_name 不存在时，创建一个新的 vector store
        with self._lock:
            if self._vector_stores.get(index_name) is None:
                self._vector_stores[index_name] = Weaviate(
                    client=self._client,
                    index_name=index_name,
                    text_key="text", # TODO: 这是啥？
                    embedding=get_embeddings_model(), #TODO： 嵌入模型也是一个资源型变量吗？ 需要单例化吗？
                    by_text=False,
                    attributes=["source", "title"],
                )

            return self._vector_stores[index_name]

    
    def is_ready(self) -> bool:
        """Check if the Weaviate connection is ready."""
        try:
            return self._client.is_ready() if self._client else False
        except Exception:
            return False




# # 在应用启动时，创建一个全局的管理器实例
# vector_store_manager = VectorStoreManager()


# --- 在应用的其他地方使用 ---

# 文件名: app/main.py (例如一个 FastAPI 应用)
# from app.vector_store_manager import vector_store_manager

# @app.post("/chat/{knowledge_base_id}")
# def handle_chat(knowledge_base_id: str, query: str):
#     # 动态地从管理器获取与特定知识库对应的 vector store
#     # knowledge_base_id 就可以是你的 index_name
#     current_vector_store = vector_store_manager.get_store(knowledge_base_id)
#     
#     retriever = current_vector_store.as_retriever()
#     # ... 后续逻辑 ...

