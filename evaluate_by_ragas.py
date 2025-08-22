import json
import weaviate
import os
import argparse

from typing import Any, Dict, Optional
from tqdm import tqdm
from langchain_deepseek import ChatDeepSeek
from langchain_community.embeddings import ZhipuAIEmbeddings
from langchain_core.retrievers import BaseRetriever
from operator import itemgetter
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from ragas import EvaluationDataset, evaluate
from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness
from langchain_community.vectorstores import Weaviate


TEMPLATE =  """Answer the following question based on this context:

{context}

Question: {question}
"""

class MyRAG:
    def __init__(self, retriever:BaseRetriever):
        self.llm = ChatDeepSeek(model="deepseek-chat", temperature=0, max_tokens=4096)
        self.embeddings = ZhipuAIEmbeddings(model="embedding-3", dimensions=1024) # type: ignore
        self.doc_embeddings = None
        self.docs = None
        self.retriever = retriever


        prompt = ChatPromptTemplate.from_template(TEMPLATE) 

        def format_docs(docs):
            # return "\n\n".join([f"Title: {d.metadata.get('title', '')}\nSource: {d.metadata.get('source', '')}\n\n{d.page_content}" for d in docs])
            return "\n\n".join([f"{d}" for d in docs])


        rag_chain = (
            {'context': itemgetter("contexts") | RunnableLambda(format_docs),
            'question': itemgetter('question')}
            | prompt
            | self.llm
            | StrOutputParser()
        )


        self.rag_chain = rag_chain


    def load_scifact_data(self,data_path: str = "datasets/scifact") -> Dict[str, Any]:
        """加载 SciFact 数据集"""
        # 加载语料库
        corpus = {}
        with open(f"{data_path}/corpus.jsonl", 'r') as f:
            for line in f:
                doc = json.loads(line)
                corpus[doc["_id"]] = doc
        
        # 加载查询
        queries = {}
        with open(f"{data_path}/queries.jsonl", 'r') as f:
            for line in f:
                query = json.loads(line)
                queries[query["_id"]] = query
        
        # 加载相关性判断
        qrels = {}
        with open(f"{data_path}/qrels/test.tsv", 'r') as f:
            next(f)  # 跳过标题行
            for line in f:
                query_id, doc_id, relevance = line.strip().split('\t')
                if query_id not in qrels:
                    qrels[query_id] = {}
                qrels[query_id][doc_id] = int(relevance)
        
        return {
            "corpus": corpus,
            "queries": queries,
            "qrels": qrels
        }

    def prepare_ragas_dataset(self, data: Dict[str, Any], sample_size: Optional[int] = None, based_on_all_relevance: bool = True) -> EvaluationDataset:
        """准备 RAGAS 评估数据集"""
        ragas_data = []
        
        query_ids = list(data["qrels"].keys())
        if sample_size:
            query_ids = query_ids[:sample_size]
        
        for query_id in tqdm(query_ids, desc="准备评估数据"):
            query = data["queries"][query_id]
            relevant_docs = data["qrels"][query_id]
            
            # 获取检索到的文档
            retrieved_docs = self.retriever.get_relevant_documents(query["text"])
            retrieved_contexts = [doc.page_content for doc in retrieved_docs]

            # get answer
            response = self.rag_chain.invoke({'question': query["text"], 'contexts': retrieved_contexts})
            
            # 获取 ground truth 文档

            ground_truth_contexts = []
            for doc_id, relevance in relevant_docs.items():
                if relevance > 0 and doc_id in data["corpus"]:
                    ground_truth_contexts.append(data["corpus"][doc_id]["text"])
            
            if based_on_all_relevance:
                reference = "\n".join(ground_truth_contexts)
            else:
                reference = ground_truth_contexts[0] if ground_truth_contexts else ""

            ragas_data.append({
                "user_input":query["text"],
                "retrieved_contexts":retrieved_contexts, 
                "response":response, # 这是问题的答案
                "reference":reference
            })
        
        return EvaluationDataset.from_list(ragas_data)


    def evaluate(self, ragas_dataset: EvaluationDataset):
        return evaluate(dataset=ragas_dataset,metrics=[LLMContextRecall(), Faithfulness(), FactualCorrectness()],llm=self.llm)
    
def get_retriever(index_name="Scifact"):
    client = weaviate.Client(
        url=os.environ["WEAVIATE_URL"],
        auth_client_secret=weaviate.AuthApiKey(api_key=os.environ["WEAVIATE_API_KEY"]),
    )

    embeddings = ZhipuAIEmbeddings(model="embedding-3", dimensions=1024) # type: ignore

    langchain_weaviate =  Weaviate(
                        client=client,
                        index_name=index_name,
                        text_key="text", 
                        embedding=embeddings, 
                        by_text=False,
                        attributes=["source", "title"],
                )

    retriever = langchain_weaviate.as_retriever(search_kwargs=dict(k=6))
    return retriever

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SciFact 生成评估")
    parser.add_argument("--sample-size", type=int, default=2, help="评估样本数量")
    parser.add_argument("--index-name", type=str, default="Scifact", help="Weaviate 索引名")
    parser.add_argument("--data_path", type=str, default="datasets/scifact", help="数据集路径")
    parser.add_argument("--output", type=str, default="generation_evaluation_results.json", help="结果输出文件")
    parser.add_argument("--based-on-all-relevance", type=bool, default=True, help="评估是否基于所有相关文档")

    args = parser.parse_args()

    retriever  = get_retriever(index_name=args.index_name)
    rag = MyRAG(retriever)
    dataset = rag.load_scifact_data(data_path=args.data_path)
    ragas_dataset = rag.prepare_ragas_dataset(dataset, sample_size=args.sample_size, based_on_all_relevance=args.based_on_all_relevance)
    results = rag.evaluate(ragas_dataset)
    
        # 保存结果
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"✅ 评估完成！结果已保存到 {args.output}")
    print("\n📊 评估结果摘要:")
    print(results)
    