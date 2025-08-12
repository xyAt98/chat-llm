from email.policy import HTTP
from fastapi import HTTPException
from langchain_core.runnables import (
    ConfigurableField,
    Runnable
)

class DynamicChain(Runnable):
    def __init__(self):
        self.chain = None

    def set_chain(self, chain):
        self.chain = chain

    def invoke(self, input):
        if self.chain is None:
            raise HTTPException(status_code=500, detail="Chain not set")
        return self.chain.invoke(input)
    
    # TODO: 这里我是不是得把 所有的方法都重新定义一下？
    
dynamic_chain = DynamicChain()