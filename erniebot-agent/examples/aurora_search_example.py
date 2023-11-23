import argparse
import asyncio

from erniebot_agent.agents.functional_agent import FunctionalAgent
from erniebot_agent.chat_models.erniebot import ERNIEBot
from erniebot_agent.memory.whole_memory import WholeMemory
from erniebot_agent.retrievers.aurora_search import AuroraSearch
from erniebot_agent.retrievers.document import Document
from erniebot_agent.tools.aurora_tool import AuroraSearchTool, AuroraSearchToolInputView
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import SpacyTextSplitter

import erniebot

parser = argparse.ArgumentParser()
parser.add_argument("--base_url", type=str, help="The Aurora serving path.")
parser.add_argument("--data_path", default="construction_regulations", type=str, help="The data path.")
parser.add_argument(
    "--access_token", default="ai_studio_access_token", type=str, help="The aistudio access token."
)
parser.add_argument("--api_type", default="qianfan", type=str, help="The aistudio access token.")
parser.add_argument("--api_key", default="", type=str, help="The API Key.")
parser.add_argument("--secret_key", default="", type=str, help="The secret key.")
parser.add_argument("--indexing", action="store_true", help="The indexing step.")
parser.add_argument("--project_id", default=-1, type=int, help="The API Key.")

args = parser.parse_args()


def offline_ann(data_path, aurora_db):
    loader = PyPDFDirectoryLoader("construction_regulations")
    documents = loader.load()
    text_splitter = SpacyTextSplitter(pipeline="zh_core_web_sm", chunk_size=1500, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)
    list_data = []
    for item in docs:
        doc_title = item.metadata["source"].split("/")[-1]
        doc_content = item.page_content
        example = {"title": doc_title, "content_se": doc_content}
        example = Document.from_dict(example)
        list_data.append(example)

    res = aurora_db.indexing(list_data=list_data)
    return res


if __name__ == "__main__":
    aurora_db = AuroraSearch(
        baseUrl=args.base_url,
        projectName="construction_data",
        remark="construction test dataset",
        projectId=args.project_id,
    )
    if args.indexing:
        offline_ann(args.data_path, aurora_db)

    query = "城乡建设部规章中描述的城市管理执法的执法主体是谁？"
    # One example
    # list_data = [{'id': '1', 'title': '城市管理执法办法',
    #               'content_se': '第一条 为了规范城市管理执法工作，提高执法和服务水平，\
    #                 维护城市管理秩序，保护公民、法人和其他组织的合法权益，\
    #               根据行政处罚法、行政强制法等法律法规的规定，制定本办法。'}]
    # Doc store test
    result = aurora_db.search(query=query, top_k=3, filters=None)
    print(result)
    # Field description
    field_map = {
        "query": {"type": str, "description": "查询语句"},
        "top_k": {"type": int, "description": "返回结果数量"},
    }
    input_view = AuroraSearchToolInputView.from_dict(field_map=field_map)
    print(input_view.function_call_schema())

    if args.api_type == "aistudio":
        erniebot.api_type = "aistudio"
        erniebot.access_token = args.access_token
    elif args.api_type == "qianfan":
        erniebot.api_type = "qianfan"
        erniebot.ak = args.api_key
        erniebot.sk = args.secret_key

    # Few shot examples
    few_shot_examples = [
        {
            "user": "城乡建设部规章中描述的城市管理执法的执法主体是谁？",
            "thoughts": "这是一个住房和城乡建设部规章的问题，我们使用AuroraSearchTool工具检索相关的信息，检索的query：'城市管理执法的执法主体'}",
            "arguments": '{"query": "城市管理执法的执法主体", "top_k": 3}',
        }
    ]

    aurora_search = AuroraSearchTool(
        description="在住房和城乡建设部规章中寻找和query最相关的片段",
        db=aurora_db,
        input_type=input_view,
        examples=few_shot_examples,
    )
    print(aurora_search.function_call_schema())
    # Tool Test
    result = asyncio.run(aurora_search(query=query))
    llm = ERNIEBot(model="ernie-bot-8k")
    memory = WholeMemory()
    # Agent test
    agent = FunctionalAgent(llm=llm, tools=[aurora_search], memory=memory)
    response = asyncio.run(agent.async_run(query))
    print(response)