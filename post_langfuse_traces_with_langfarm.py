import logging
import os
import time

from dotenv import load_dotenv
from langchain_community.llms import Tongyi
from langchain_core.output_parsers import JsonOutputParser
from langfarm.hooks.langfuse.callback import CallbackHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(verbose=True)

query = '把 a = b + c 转成 json 对象。不需要多余的解释。'
llm = Tongyi(model="qwen-plus", api_key=os.getenv("DASHSCOPE_API_KEY"))
langfuse_handler = CallbackHandler()
chain = llm | JsonOutputParser()
r = chain.invoke(query, config={"callbacks": [langfuse_handler]})
logger.info("Tongyi 输出 -> %s", r)
s = 2
logger.info("等待 %d 秒，等待 langfuse 异步上报。", s)
langfuse_handler.flush()
time.sleep(s)
logger.info("langfuse shutdown ...")
langfuse_handler.langfuse.shutdown()
logger.info("langfuse shutdown end")
