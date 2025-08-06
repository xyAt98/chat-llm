from chain import answer_chain

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
    answer_correctness
)

metrics = [
    faithfulness, 
    answer_relevancy, # 答案跟上下文的相关性
    context_recall, # 检索到的文档的覆盖度， 召回的/总共的
    context_precision, # 检索到的文档的准确性
    answer_correctness # 答案的正确性， 应该是跟真实答案进行比较
]

# 我得通过调用后端接口来拿到 rag 的答案和索引文档吗？ 我猜是的


# 默认用 OpenAI 作为“裁判”的话， 我这应该用不了吧
result = evaluate(metrics, "./data/evaluation.jsonl")
