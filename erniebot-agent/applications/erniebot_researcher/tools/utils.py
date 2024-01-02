import os
import urllib.parse
from typing import Optional

import erniebot
import jsonlines
from langchain.docstore.document import Document
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import SpacyTextSplitter
from langchain.vectorstores import FAISS

# from erniebot_agent.retrieval.document import Document
from md2pdf.core import md2pdf
from sklearn.metrics.pairwise import cosine_similarity

<<<<<<< Updated upstream:erniebot-agent/applications/erniebot_researcher/tools/utils.py
from erniebot_agent.retrieval.document import Document

embeddings = OpenAIEmbeddings(deployment="text-embedding-ada")
api_type = os.environ.get("api_type", None)
access_token = os.environ.get("access_token", None)


=======
# from erniebot_agent.retrieval.document import Document
>>>>>>> Stashed changes:erniebot-agent/applications/erniebot_researcher/tools/utils.py
class FaissSearch:
    def __init__(self, db,embeddings):
        self.db = db
        self.embeddings=embeddings
    def search(self, query: str, top_k: int = 10, **kwargs):
        docs=self.db.similarity_search(query, top_k)
        para_result = self.embeddings.embed_documents([i.page_content for i in docs])
        query_result = self.embeddings.embed_query(query)
        similarities = cosine_similarity([query_result], para_result).reshape((-1,))
        retrieval_results = []
        for index, doc in enumerate(docs):
            retrieval_results.append(
                {
                    "content": doc.page_content,
                    "score": similarities[index],
                    "title": doc.metadata["name"],
                    "url": doc.metadata["url"],
                }
            )
        return retrieval_results


def build_index(faiss_name, embeddings,path=None, abstract=False, origin_data=None, use_data=False):
    if os.path.exists(faiss_name):
        db = FAISS.load_local(faiss_name, embeddings)
    elif abstract and not use_data:
        all_docs = []
        with jsonlines.open(path) as reader:
            for obj in reader:
                if type(obj) == list:
                    for item in obj:
                        if "url" in item:
                            metadata = {"url": item["url"], "name": item["name"]}
                        else:
                            metadata = {"name": item["name"]}
                        doc = Document(page_content=item["page_content"], metadata=metadata)
                        all_docs.append(doc)
                elif type(obj) == dict:
                    if "url" in obj:
                        metadata = {"url": obj["url"], "name": obj["name"]}
                    else:
                        metadata = {"name": obj["name"]}
                    doc = Document(page_content=obj["page_content"], metadata=metadata)
                    all_docs.append(doc)
        db = FAISS.from_documents(all_docs, embeddings)
        db.save_local(faiss_name)
    elif not abstract and not use_data:
        loader = PyPDFDirectoryLoader(path)
        documents = loader.load()
        text_splitter = SpacyTextSplitter(pipeline="zh_core_web_sm", chunk_size=1500, chunk_overlap=0)
        docs = text_splitter.split_documents(documents)
        docs_tackle = []
        for item in docs:
            item.metadata["name"] = item.metadata["source"].split("/")[-1].replace(".pdf", "")
            item.metadata["url"] = item.metadata["source"]
            docs_tackle.append(item)
        db = FAISS.from_documents(docs_tackle, embeddings)
        db.save_local(faiss_name)
    elif use_data:
        db = FAISS.from_documents(origin_data, embeddings)
        db.save_local(faiss_name)
    return db


def erniebot_chat(messages: list, functions: Optional[str] = None, model: Optional[str] = None, **kwargs):
    if not model:
        model = "ernie-3.5"
    _config = dict(
        api_type=api_type,
        access_token=access_token,
    )
    if functions is None:
        resp_stream = erniebot.ChatCompletion.create(
            _config_=_config, model=model, messages=messages, **kwargs, stream=False
        )
    else:
        resp_stream = erniebot.ChatCompletion.create(
            _config_=_config, model=model, messages=messages, **kwargs, functions=functions, stream=False
        )
    return resp_stream["result"]


def call_function(action: str, agent_role_prompt: str, model="ernie-longtext", **kwargs):
    messages = [
        {
            "role": "user",
            "content": action,
        }
    ]
    answer = erniebot_chat(messages, system=agent_role_prompt, model=model, **kwargs)
    return answer


def write_to_file(filename: str, text: str) -> None:
    """Write text to a file

    Args:
        text (str): The text to write
        filename (str): The filename to write to
    """
    with open(filename, "w") as file:
        file.write(text)


def md_to_pdf(input_file, output_file):
    md2pdf(output_file, md_content=None, md_file_path=input_file, css_file_path=None, base_url=None)


def write_md_to_pdf(task: str, path: str, text: str) -> str:
    file_path = f"{path}/{task}"
    write_to_file(f"{file_path}.md", text)

    # encoded_file_path = urllib.parse.quote(f"{file_path}.pdf")
    encoded_file_path = urllib.parse.quote(f"{file_path}.md")
    return encoded_file_path


def write_to_json(filename: str, list_data: list, mode="w") -> None:
    """Write text to a file

    Args:
        text (str): The text to write
        filename (str): The filename to write to
    """
    with jsonlines.open(filename, mode) as file:
        for item in list_data:
            file.write(item)


def json_correct(json_data):
    messages = [{"role": "user", "content": "请纠正以下数据的json格式：" + json_data}]
    res = erniebot_chat(messages)
    start_idx = res.index("{")
    end_idx = res.rindex("}")
    corrected_data = res[start_idx : end_idx + 1]
    return corrected_data


def add_citation(paragraphs, faiss_name):
    list_data = []
    for item in paragraphs:
        if "url" in item:
            metadata = {"url": item["url"], "name": item["name"]}
        else:
            metadata = {"name": item["name"]}
        doc = Document(page_content=item["summary"], metadata=metadata)
        list_data.append(doc)
    db = build_index(faiss_name=faiss_name, origin_data=list_data, use_data=True)
    res = FaissSearch(db)
    return res


if "__main__" == __name__:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--OPENAI_API_TYPE", type=str, default="", help="")
    parser.add_argument("--OPENAI_API_BASE", type=str, default="", help="")
    parser.add_argument("--OPENAI_API_KEY", type=str, default="", help="")
    parser.add_argument("--OPENAI_API_VERSION", type=str, default="", help="")
    parser.add_argument("--faiss_name_paper", type=str, default="", help="")
    parser.add_argument("--faiss_name_abstract", type=str, default="", help="")
    parser.add_argument("--faiss_path_paper", type=str, default="", help="")
    parser.add_argument("--faiss_path_abstract", type=str, default="", help="")
    args = parser.parse_args()
    import os

    os.environ["OPENAI_API_TYPE"] = args.OPENAI_API_TYPE
    os.environ["OPENAI_API_BASE"] = args.OPENAI_API_BASE
    os.environ["OPENAI_API_KEY"] = args.OPENAI_API_KEY
    os.environ["OPENAI_API_VERSION"] = args.OPENAI_API_VERSION
    paper_db = build_index(faiss_name=args.faiss_name_paper, path=args.faiss_path_paper)
    abstract_db = build_index(
        faiss_name=args.faiss_name_abstract, path=args.faiss_path_abstract, abstract=True
    )
