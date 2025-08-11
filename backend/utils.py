import os
from langchain_core.embeddings import Embeddings
# from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import ZhipuAIEmbeddings

def get_embeddings_model() -> Embeddings:
    return ZhipuAIEmbeddings(model="embedding-3", dimensions=1024, api_key=os.environ["ZHIPUAI_API_KEY"])
    # return OpenAIEmbeddings(model="text-embedding-3-small", chunk_size=200)