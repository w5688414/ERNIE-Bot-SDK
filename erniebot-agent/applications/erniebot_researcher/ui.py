import argparse
import asyncio
import hashlib
import os

import gradio as gr
import jsonlines
from EditorActorAgent import EditorActorAgent
from RankingAgent import RankingAgent
from ResearchAgent import ResearchAgent
from ReviserActorAgent import ReviserActorAgent
from tools.intent_detection_tool import IntentDetectionTool
from tools.outline_generation_tool import OutlineGenerationTool
from tools.ranking_tool import TextRankingTool
from tools.report_writing_tool import ReportWritingTool
from tools.semantic_citation_tool import SemanticCitationTool
from tools.summarization_tool import TextSummarizationTool
from tools.task_planning_tool import TaskPlanningTool
from tools.utils import write_md_to_pdf
<<<<<<< Updated upstream:erniebot-agent/applications/erniebot_researcher/ui.py

from erniebot_agent.retrieval.baizhong_search import BaizhongSearch
from erniebot_agent.tools.baizhong_tool import BaizhongSearchTool

=======
from langchain.embeddings.openai import OpenAIEmbeddings
>>>>>>> Stashed changes:erniebot-agent/applications/erniebot_researcher/ui.py
parser = argparse.ArgumentParser()
parser.add_argument("--api_type", type=str, default="aistudio")

parser.add_argument("--knowledge_base_name_paper", type=str, default="", help="")
parser.add_argument("--knowledge_base_name_abstract", type=str, default="", help="")
parser.add_argument("--knowledge_base_id_paper", type=str, default="", help="")
parser.add_argument("--knowledge_base_id_abstract", type=str, default="", help="")

parser.add_argument("--faiss_name_paper", type=str, default="", help="")
parser.add_argument("--faiss_name_abstract", type=str, default="", help="")
parser.add_argument("--faiss_name_citation", type=str, default="", help="")

parser.add_argument("--iterations", type=int, default=4, help="")
parser.add_argument("--num_research_agent", type=int, default=2, help="The number of research agent")
parser.add_argument(
    "--report_type",
    type=str,
    default="research_report",
    help="['research_report','resource_report','outline_report']",
)

parser.add_argument("--OPENAI_API_TYPE", type=str, default="", help="")
parser.add_argument("--OPENAI_API_BASE", type=str, default="", help="")
parser.add_argument("--OPENAI_API_KEY", type=str, default="", help="")
parser.add_argument("--OPENAI_API_VERSION", type=str, default="", help="")

parser.add_argument("--server_name", type=str, default="0.0.0.0")
parser.add_argument("--server_port", type=int, default=8878)

parser.add_argument('--embedding_type',type=str,default='open_embedding',help="['open_embedding','baizhong','ernie_embedding']")

args = parser.parse_args()

api_type = args.api_type
access_token = args.access_token
# api_type = os.environ.get("api_type", None)
# access_token = os.environ.get("access_token", None)
os.environ["OPENAI_API_TYPE"] = args.OPENAI_API_TYPE
os.environ["OPENAI_API_BASE"] = args.OPENAI_API_BASE
os.environ["OPENAI_API_KEY"] = args.OPENAI_API_KEY
os.environ["OPENAI_API_VERSION"] = args.OPENAI_API_VERSION
os.environ["api_type"] = api_type
os.environ["access_token"] = access_token
import jsonlines
from erniebot_agent.retrieval import BaizhongSearch
from EditorActorAgent import EditorActorAgent
from RankingAgent import RankingAgent
from ResearchAgent import ResearchAgent
from ReviserActorAgent import ReviserActorAgent
from tools.intent_detection_tool import IntentDetectionTool
from tools.outline_generation_tool import OutlineGenerationTool
from tools.ranking_tool import TextRankingTool
from tools.report_writing_tool import ReportWritingTool
from tools.semantic_citation_tool import SemanticCitationTool
from tools.summarization_tool import TextSummarizationTool
from tools.task_planning_tool import TaskPlanningTool
from tools.utils import FaissSearch, build_index, write_md_to_pdf


def get_logs(jsonl_file="./outputs/erniebot/log.jsonl"):
    history = []
    with jsonlines.open(jsonl_file, "r") as file:
        for item in file:
            history.append(item)
    return history


def generate_report(query, history=[]):
    if args.embedding_type=="open_embedding":
        embeddings = OpenAIEmbeddings(deployment="text-embedding-ada")
        paper_db = build_index(faiss_name=args.faiss_name_paper,embeddings=embeddings)
        abstract_db = build_index(faiss_name=args.faiss_name_abstract,embeddings=embeddings)
        abstract_search = FaissSearch(abstract_db,embeddings=embeddings)
        retriever_search = FaissSearch(paper_db,embeddings=embeddings)
    elif args.embedding_type=="ernie_embedding":
        embeddings = ErnieEmbeddings(aistudio_access_token=access_token)
        paper_db = build_index(faiss_name=args.faiss_name_paper,embeddings=embeddings)
        abstract_db = build_index(faiss_name=args.faiss_name_abstract,embeddings=embeddings)
        abstract_search = FaissSearch(abstract_db,embeddings=embeddings)
        retriever_search = FaissSearch(paper_db,embeddings=embeddings)
    elif args.embedding_type=='baizhong':
        retriever_search = BaizhongSearch(
            access_token=access_token,
            knowledge_base_name=args.knowledge_base_name_paper,
            knowledge_base_id=args.knowledge_base_id_paper,)
        abstract_search=BaizhongSearch(
            access_token=access_token,
            knowledge_base_name=args.knowledge_base_name_abstract,
            knowledge_base_id=args.knowledge_base_id_abstract,)

    intent_detection_tool = IntentDetectionTool()
    outline_generation_tool = OutlineGenerationTool()
    ranking_tool = TextRankingTool()
    report_writing_tool = ReportWritingTool()
    summarization_tool = TextSummarizationTool()
    task_planning_tool = TaskPlanningTool()
    semantic_citation_tool = SemanticCitationTool()
    dir_path = f"./outputs/erniebot/{hashlib.sha1(query.encode()).hexdigest()}"
    target_path = f"./outputsl/erniebot/{hashlib.sha1(query.encode()).hexdigest()}/revised"
    os.makedirs(target_path, exist_ok=True)
    os.makedirs(dir_path, exist_ok=True)
    research_actor = []
    for i in range(args.num_research_agent):
        agents_name = "agent_" + str(i)
        research_agent = ResearchAgent(
            name="generate_report",
            agent_name=agents_name,
            system_message="你是一个报告生成助手。你可以根据用户的指定内容生成一份报告手稿",
            dir_path=dir_path,
            report_type=args.report_type,
            retriever_abstract_tool=abstract_search,
            retriever_tool=retriever_search,
            intent_detection_tool=intent_detection_tool,
            task_planning_tool=task_planning_tool,
            report_writing_tool=report_writing_tool,
            outline_tool=outline_generation_tool,
            citation_tool=semantic_citation_tool,
            summarize_tool=summarization_tool,
            faiss_name_citation=args.faiss_name_citation,
            save_log_path="./outputs/erniebot/log.jsonl",
        )
        research_actor.append(research_agent)
    editor_actor = EditorActorAgent(name="editor", save_log_path="./outputs/erniebot/log.jsonl")
    reviser_actor = ReviserActorAgent(name="reviser", save_log_path="./outputs/erniebot/log.jsonl")
    ranker_actor = RankingAgent(
        name="ranker",
        ranking_tool=ranking_tool,
        save_log_path="./outputs/erniebot/log.jsonl",
    )
    list_reports = []
    for researcher in research_actor:
        report, _ = asyncio.run(researcher._async_run(query))
        list_reports.append(report)
    breakpoint()
    for i in range(args.iterations):
        if len(list_reports) > 1:
            list_reports, immedia_report = asyncio.run(ranker_actor._async_run(list_reports, query))
        else:
            immedia_report = list_reports[0]
        revised_report = immedia_report
        if i == 0:
            markdown_report = immedia_report
        else:
            markdown_report = revised_report
        respose = asyncio.run(editor_actor._async_run(markdown_report))
        if respose["accept"] is True:
            break
        else:
            revised_report = asyncio.run(reviser_actor._async_run(markdown_report, respose["notes"]))
            list_reports.append(revised_report)
    path = write_md_to_pdf(args.report_type, target_path, revised_report)
    return revised_report, path


def launch_ui():
    with gr.Blocks(title="报告生成小助手", theme=gr.themes.Base()) as demo:
        gr.HTML("""<h1 align="center">generation report小助手</h1>""")
        with gr.Row():
            with gr.Column():
                gr.Dropdown(
                    choices=[
                        "research_agent",
                        "editor_agent",
                        "ranking_agent",
                        "reviser_agent",
                        "user_agent",
                    ],
                    multiselect=True,
                    label="agents",
                    info="",
                )
        report = gr.Markdown(label="生成的report")
        report_url = gr.File(label="原文下载链接")
        with gr.Row():
            with gr.Column():
                query_textbox = gr.Textbox(placeholder="写一份关于机器学习发展的报告")
                gr.Examples(
                    [["大模型相关技术研究"], ["写一份数字经济发展的报告"], ["写一份关于机器学习发展的报告"]],
                    inputs=[query_textbox],
                    outputs=[query_textbox],
                    label="示例输入",
                )
            with gr.Row():
                submit = gr.Button("🚀 提交", variant="primary", scale=1)
                clear = gr.Button("清除", variant="primary", scale=1)
            submit.click(generate_report, inputs=[query_textbox], outputs=[report, report_url])
            clear.click(lambda _: ([None, None]), outputs=[report, report_url])
        recording = gr.Chatbot(label="历史记录")
        with gr.Row():
            clear_recoding = gr.Button(value="记录清除")
            submit_recoding = gr.Button(value="记录更新")
        submit_recoding.click(get_logs, inputs=[], outputs=[recording])
        clear_recoding.click(lambda _: ([[None, None]]), outputs=[recording])
    demo.launch(server_name=args.server_name, server_port=args.server_port)


if "__main__" == __name__:
    launch_ui()
