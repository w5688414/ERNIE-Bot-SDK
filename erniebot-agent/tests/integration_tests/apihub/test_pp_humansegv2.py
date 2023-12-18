from __future__ import annotations

import pytest
from erniebot_agent.file_io import get_file_manager
from erniebot_agent.tools import RemoteToolkit

from .base import RemoteToolTesting


class TestRemoteTool(RemoteToolTesting):
    @pytest.mark.asyncio
    async def test_humanseg(self):
        toolkit = RemoteToolkit.from_aistudio("humanseg")
        tools = toolkit.get_tools()
        print(tools[0].function_call_schema())

        agent = self.get_agent(toolkit)

        file_manager = get_file_manager()
        file_path = self.download_file(
            "https://paddlenlp.bj.bcebos.com/ebagent/ci/fixtures/remote-tools/humanseg_input_img.jpg"
        )
        file = await file_manager.create_file_from_path(file_path)

        result = await agent.async_run("对这张图片进行人像分割，包含的文件为：", files=[file])
        self.assertEqual(len(result.files), 2)
        self.assertEqual(len(result.actions), 1)
        self.assertIn("file-", result.text)
