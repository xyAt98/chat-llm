"""Load html from files, clean up, split, ingest into Weaviate."""
import logging
import os
import re
from pathlib import Path

from regex import B
from parser import langchain_docs_extractor
from beir import util


import weaviate
from bs4 import BeautifulSoup, SoupStrainer
from constants import WEAVIATE_DOCS_INDEX_NAME, WEAVIATE_WANG_DEATH_BOOK, WEAVIATE_SCIFACT_INDEX_NAME
from langchain.indexes import SQLRecordManager, index
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.utils.html import PREFIXES_TO_IGNORE_REGEX, SUFFIXES_TO_IGNORE_REGEX
from langchain_community.vectorstores import Weaviate
from langchain_core.embeddings import Embeddings
# from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import ZhipuAIEmbeddings
from langchain.document_loaders import (
    RecursiveUrlLoader,
    SitemapLoader,
    TextLoader,
    JSONLoader,
)

root_dir = Path(__file__).parent.parent
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BATCH_SIZE = 64

def get_embeddings_model() -> Embeddings:
    return ZhipuAIEmbeddings(model="embedding-3", dimensions=1024)
    # return OpenAIEmbeddings(model="text-embedding-3-small", chunk_size=200)


def metadata_extractor(meta: dict, soup: BeautifulSoup) -> dict:
    title = soup.find("title")
    description = soup.find("meta", attrs={"name": "description"})
    html = soup.find("html")
    return {
        "source": meta["loc"],
        "title": title.get_text() if title else "",
        "description": description.get("content", "") if description else "",
        "language": html.get("lang", "") if html else "",
        **meta,
    }


def load_langchain_docs():
    langchain_docs = SitemapLoader(
        "https://python.langchain.com/sitemap.xml",
        filter_urls=["https://python.langchain.com/"],
        parsing_function=langchain_docs_extractor,
        default_parser="lxml",
        bs_kwargs={
            "parse_only": SoupStrainer(
                name=("article", "title", "html", "lang", "content")
            ),
        },
        meta_function=metadata_extractor,
    ).load()
    return langchain_docs


def load_langsmith_docs():
    langsmith_docs = RecursiveUrlLoader(
        url="https://docs.smith.langchain.com/",
        max_depth=2,
        extractor=simple_extractor,
        prevent_outside=True,
        use_async=True,
        timeout=600,
        # Drop trailing / to avoid duplicate pages.
        link_regex=(
            f"href=[\"']{PREFIXES_TO_IGNORE_REGEX}((?:{SUFFIXES_TO_IGNORE_REGEX}.)*?)"
            r"(?:[\#'\"]|\/[\#'\"])"
        ),
        check_response_status=True,
    ).load()
    return langsmith_docs


def simple_extractor(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    return re.sub(r"\n\n+", "\n\n", soup.text).strip()


def load_api_docs():
    api_docs = RecursiveUrlLoader(
        url="https://api.python.langchain.com/en/latest/",
        max_depth=2,
        extractor=simple_extractor,
        prevent_outside=True,
        use_async=True,
        timeout=600,
        # Drop trailing / to avoid duplicate pages.
        link_regex=(
            f"href=[\"']{PREFIXES_TO_IGNORE_REGEX}((?:{SUFFIXES_TO_IGNORE_REGEX}.)*?)"
            r"(?:[\#'\"]|\/[\#'\"])"
        ),
        check_response_status=True,
        exclude_dirs=(
            "https://api.python.langchain.com/en/latest/_sources",
            "https://api.python.langchain.com/en/latest/_modules",
        ),
    ).load()
    return api_docs

def load_docs_from_book(path: str) -> dict:
    base = Path(path)

    # 文本/Markdown 文档
    book_docs = TextLoader(
        file_path='/home/yani/Downloads/王氏之死.txt',
        encoding='utf-8').load()
    return book_docs

    # 给每个 Document 加上自定义 metadata
    # for doc in docs_text:
    #     # 路径、文件名
    #     src = doc.metadata.get("source", doc.metadata.get("file_path", ""))
    #     doc.metadata.update({
    #         "source": src,
    #         "title": Path(src).stem,   # 文件名（不含扩展名）当做 title
    #     })
    #     # 如果你需要用之前写的 metadata_extractor，还可以：
    #     # doc.metadata.update(metadata_extractor(doc.metadata, BeautifulSoup(doc.page_content, 'lxml')))


# def load_docs_from_beir_and_index_to_weaviate(dataset_name: str = "scifact"):
#     # 我得实现 index 的这个功能
#     WEAVIATE_URL = os.environ["WEAVIATE_URL"]
#     WEAVIATE_API_KEY = os.environ["WEAVIATE_API_KEY"]
#     RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]

#     # download beir dataset if path does not exist
#     datasets_dir = os.path.join(root_dir, "datasets")
#     if not os.path.exists(os.path.join(datasets_dir, dataset_name)):
#         url = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{}.zip".format(dataset_name)
#         dataset_path = util.download_and_unzip(url, datasets_dir)
#         print(f"Dataset {dataset_name} downloaded to {dataset_path}")

#     # load beir dataset
#     from beir.datasets.data_loader import GenericDataLoader
#     corpus, queries, qrels = GenericDataLoader(data_folder=dataset_path).load(split="test")
    
#     # get weaviate client and embedding
#     client = weaviate.Client(
#         url=WEAVIATE_URL,
#         auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
#     )

#     print(f"================== {client.is_ready()} ======================")

#     embedding = get_embeddings_model()

#     # create weaviate class
#     class_obj = {
#         "class": dataset_name,
#         "vectorizer": "none",  # 重要！我们自己在客户端进行向量化
#         "properties": [
#             {
#                 "name": "beir_id",
#                 "dataType": ["text"], # 用来存储 BEIR 中的 _id
#             },
#             {
#                 "name": "title",
#                 "dataType": ["text"],
#             },
#             {
#                 "name": "content",
#                 "dataType": ["text"],
#             },
#         ],
#     }

#     # config batch load
#     client.batch.configure(
#         batch_size=100,  # default 100
#         dynamic=True # 自动调整批量大小
#     )

#     from tqdm import tqdm
#     with client.batch as batch:
#         for doc_id, doc_data in tqdm(corpus.items(), desc="Indexing to Weaviate"):
#             # 准备要存入 Weaviate 的数据对象
#             properties = {
#                 "beir_id": doc_id, # beir 的语料库里每条数据有一个ID， 要不要直接用那个
#                 "title": doc_data.get("title", ""),
#                 "content": doc_data.get("text", ""),
#             }
        
#             text_to_embed = f"{doc_data['title']}\n\n{doc_data['text']}"
            
#             # 这里是 embed 一条数据吗？
#             vector = embedding.embed_query(text_to_embed)
#             batch.add_data_object(
#                 data_object=properties,
#                 class_name=dataset_name,
#                 vector=vector
#             )
        

def load_json_docs(path: str):
    def metadata_func(json_obj, default_metadata):
        return {
            **default_metadata,
            "corpus_id": json_obj["_id"],
            "title": json_obj["title"],
        }

    loader = JSONLoader(
        file_path=path,
        jq_schema=".",
        content_key="text",
        metadata_func=metadata_func,
        json_lines=True
    )
    docs = loader.load()

    return docs

def ingest_docs(index_name: str):
    # 这个只能用langchain的loader加载并向量化保存到 weaviate 中， 封装得太多了。
    WEAVIATE_URL = os.environ["WEAVIATE_URL"]
    WEAVIATE_API_KEY = os.environ["WEAVIATE_API_KEY"]
    RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
    embedding = get_embeddings_model()

    client = weaviate.Client(
        url=WEAVIATE_URL,
        auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
    )
    print(f"================== {client.is_ready()} ======================")
    vectorstore = Weaviate(
        client=client,
        index_name=index_name,
        text_key="text",
        embedding=embedding,
        by_text=False,
        attributes=["source", "title"],
    )

    record_manager = SQLRecordManager(
        # f"weaviate/{WEAVIATE_DOCS_INDEX_NAME}", db_url=RECORD_MANAGER_DB_URL
        f"weaviate/{index_name}", db_url=RECORD_MANAGER_DB_URL, 
    )
    record_manager.create_schema()

    # docs_from_documentation = load_langchain_docs()
    # logger.info(f"Loaded {len(docs_from_documentation)} docs from documentation")
    # docs_from_api = load_api_docs()
    # logger.info(f"Loaded {len(docs_from_api)} docs from API")
    # docs_from_langsmith = load_langsmith_docs()
    # logger.info(f"Loaded {len(docs_from_langsmith)} docs from Langsmith")

    # docs_transformed = text_splitter.split_documents(
    #     # docs_from_documentation + docs_from_api + docs_from_langsmith
    #     # docs_from_api
    #     docs_from_langsmith

    # )
    # docs_transformed = [doc for doc in docs_transformed if len(doc.page_content) > 10]

    # book_docs = load_docs_from_book('/home/yani/Downloads/王氏之死.txt')
    # logger.info(f"Loaded {len(book_docs)} docs from book")
    # book_docs_transformed = text_splitter.split_documents(book_docs)

    # docs_transformed = [doc for doc in book_docs_transformed if len(doc.page_content) > 10]
    path = "/home/yani/projects/chat-llm/datasets/scifact/corpus.jsonl"
    beir_docs = load_json_docs(path)
    logger.info(f"Loaded {len(beir_docs)} docs from beir")
    docs_transformed = text_splitter.split_documents(beir_docs)
    docs_transformed = [doc for doc in docs_transformed if len(doc.page_content) > 10]

    # We try to return 'source' and 'title' metadata when querying vector store and
    # Weaviate will error at query time if one of the attributes is missing from a
    # retrieved document.
    for doc in docs_transformed:
        if "source" not in doc.metadata:
            doc.metadata["source"] = ""
        if "title" not in doc.metadata:
            doc.metadata["title"] = ""

    indexing_stats = index(
        docs_transformed,
        record_manager,
        vectorstore,
        batch_size=BATCH_SIZE,
        cleanup="full",
        source_id_key="source",
        force_update=(os.environ.get("FORCE_UPDATE") or "false").lower() == "true",
    )

    logger.info(f"Indexing stats: {indexing_stats}")
    num_vecs = client.query.aggregate(index_name).with_meta_count().do()
    logger.info(
        f"LangChain now has this many vectors: {num_vecs}",
    )



if __name__ == "__main__":
    # ingest_docs()
    # load_docs_from_book("assets/books")
    # langsmith_docs = load_langsmith_docs()
    # api_docs = load_api_docs()
    # langchain_docs = load_langchain_docs()


    # print(f"{Path(__file__).parent.parent}")

    ingest_docs(index_name=WEAVIATE_SCIFACT_INDEX_NAME)

    print(1)

