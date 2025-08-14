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

    def invoke(self, input, config=None):
        if self.chain is None:
            raise HTTPException(status_code=500, detail="Chain not set")
        return self.chain.invoke(input, config)
    
            
dynamic_chain = DynamicChain()