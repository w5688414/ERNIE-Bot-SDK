from __future__ import annotations

import string
from typing import Type

from pydantic import Field

from erniebot_agent.tools.base import Tool
from erniebot_agent.tools.schema import ToolParameterView

from .utils import write_md_to_pdf


class SemanticCitationToolInputView(ToolParameterView):
    query: str = Field(description="Chunk of text to summarize")


class SemanticCitationToolOutputView(ToolParameterView):
    document: str = Field(description="content")


class SemanticCitationTool(Tool):
    description: str = "semantic citation tool"
    input_type: Type[ToolParameterView] = SemanticCitationToolInputView
    ouptut_type: Type[ToolParameterView] = SemanticCitationToolOutputView

    def is_punctuation(self, char: str):
        """判断一个字符是否是标点符号"""
        return char in string.punctuation

    async def __call__(
        self,
        reports: str,
        url_index: dict,
        agent_name: str,
        report_type: str,
        dir_path: str,
        citation_search,
        theta_min=0.4,
        theta_max=0.95,
        **kwargs,
    ):
        list_data = reports.split("\n\n")
        output_text = []
        for chunk_text in list_data:
            if "参考文献" in chunk_text:
                output_text.append(chunk_text)
                break
            elif "#" in chunk_text:
                output_text.append(chunk_text)
                continue
            else:
                sentence_splits = chunk_text.split("。")
                output_sent = []
                for sentence in sentence_splits:
                    if not sentence:
                        continue
                    try:
                        query_result = citation_search.search(query=sentence, top_k=1, filters=None)
                    except Exception as e:
                        output_sent.append(sentence)
                        print(e)
                        continue
                    source = query_result[0]
                    if len(sentence.strip()) > 0:
                        if not self.is_punctuation(sentence[-1]):
                            sentence += "。"
                        print(source["score"])
                        if source["score"] >= theta_min and source["score"] <= theta_max:
                            sentence += (
                                f"<sup>[\\[{url_index[source['url']]['index']}\\]]({source['url']})</sup>"
                            )
                    output_sent.append(sentence)
                chunk_text = "".join(output_sent)
                output_text.append(chunk_text)
        final_report = "\n\n".join(output_text)
        path = write_md_to_pdf(agent_name + "__" + report_type, dir_path, final_report)
        return final_report, path
