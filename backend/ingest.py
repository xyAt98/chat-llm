"""Load html from files, clean up, split, ingest into Weaviate."""
import logging
import os
import re
from pathlib import Path
from parser import langchain_docs_extractor

import weaviate
from bs4 import BeautifulSoup, SoupStrainer
from constants import WEAVIATE_DOCS_INDEX_NAME, WEAVIATE_WANG_DEATH_BOOK
from langchain_community.document_loaders import RecursiveUrlLoader, SitemapLoader
from langchain.indexes import SQLRecordManager, index
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.utils.html import PREFIXES_TO_IGNORE_REGEX, SUFFIXES_TO_IGNORE_REGEX
from langchain_community.vectorstores import Weaviate
from langchain_core.embeddings import Embeddings
# from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import ZhipuAIEmbeddings
from langchain.document_loaders import (
    TextLoader,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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



def ingest_docs():
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
        # index_name=WEAVIATE_DOCS_INDEX_NAME,
        index_name=WEAVIATE_WANG_DEATH_BOOK,
        text_key="text",
        embedding=embedding,
        by_text=False,
        attributes=["source", "title"],
    )

    record_manager = SQLRecordManager(
        # f"weaviate/{WEAVIATE_DOCS_INDEX_NAME}", db_url=RECORD_MANAGER_DB_URL
        f"weaviate/{WEAVIATE_WANG_DEATH_BOOK}", db_url=RECORD_MANAGER_DB_URL, 
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

    book_docs = load_docs_from_book('/home/yani/Downloads/王氏之死.txt')
    logger.info(f"Loaded {len(book_docs)} docs from book")
    book_docs_transformed = text_splitter.split_documents(book_docs)

    docs_transformed = [doc for doc in book_docs_transformed if len(doc.page_content) > 10]
    
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
        cleanup="full",
        source_id_key="source",
        # force_update=(os.environ.get("FORCE_UPDATE") or "false").lower() == "true",
    )

    logger.info(f"Indexing stats: {indexing_stats}")
    num_vecs = client.query.aggregate(WEAVIATE_WANG_DEATH_BOOK).with_meta_count().do()
    logger.info(
        f"LangChain now has this many vectors: {num_vecs}",
    )


if __name__ == "__main__":
    ingest_docs()
    # load_docs_from_book("assets/books")
    # langsmith_docs = load_langsmith_docs()
    # api_docs = load_api_docs()
    # langchain_docs = load_langchain_docs()


    print(1)

