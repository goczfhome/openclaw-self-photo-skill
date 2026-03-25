#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self Photo API 客户端
封装与 Self Photo 后端服务的所有 API 调用
"""

import os
import json
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

DEFAULT_BASE_URL = "http://localhost:8002"


class SelfPhotoAPIError(Exception):
    """API 错误"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class SelfPhotoClient:
    """Self Photo API 客户端"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.environ.get("SELF_PHOTO_API_KEY")
        self.base_url = base_url or os.environ.get("SELF_PHOTO_API_URL", DEFAULT_BASE_URL)

        if not self.api_key:
            raise SelfPhotoAPIError("未设置 SELF_PHOTO_API_KEY")

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None
    ) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            request_data = None
            if data:
                request_data = json.dumps(data, ensure_ascii=False).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=request_data,
                headers=headers,
                method=method
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                error_data = json.loads(error_body)
                raise SelfPhotoAPIError(
                    error_data.get("detail", f"HTTP Error {e.code}"),
                    status_code=e.code
                )
            except json.JSONDecodeError:
                raise SelfPhotoAPIError(f"HTTP Error {e.code}: {error_body}", status_code=e.code)

        except urllib.error.URLError as e:
            raise SelfPhotoAPIError(f"连接错误: {e.reason}")

    def check_balance(self) -> Dict[str, Any]:
        """检查余额"""
        return self._request("GET", "/api/balance")

    def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息（包括参考图）"""
        return self._request("GET", "/api/user")

    def upload_image(self, image_path: str) -> Dict[str, Any]:
        """上传图片"""
        import mimetypes

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")

        # 读取文件
        with open(image_path, "rb") as f:
            image_data = f.read()

        # 构建 multipart 请求
        import tempfile
        import uuid

        boundary = str(uuid.uuid4())
        body = b"--" + boundary.encode() + b"\r\n"
        body += b'Content-Disposition: form-data; name="file"; filename="' + os.path.basename(image_path).encode() + b'"\r\n'
        body += b"Content-Type: application/octet-stream\r\n\r\n"
        body += image_data + b"\r\n"
        body += b"--" + boundary.encode() + b"--\r\n"

        url = f"{self.base_url}/api/upload"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }

        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise SelfPhotoAPIError(f"上传失败: {error_body}", status_code=e.code)
        except urllib.error.URLError as e:
            raise SelfPhotoAPIError(f"连接错误: {e.reason}")

    def generate(
        self,
        prompt: str,
        image_filename: str = None,
        aspect_ratio: str = "9:16",
        resolution: str = "1k",
        user_input: str = None,
        conversations: list = None,
        role_nickname: str = None
    ) -> Dict[str, Any]:
        """生成图片"""
        data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution
        }
        if image_filename:
            data["image_filename"] = image_filename
        if user_input:
            data["user_input"] = user_input
        if conversations:
            data["conversations"] = conversations
        if role_nickname:
            data["role_nickname"] = role_nickname

        return self._request("POST", "/api/generate", data)

    def query_result(self, task_id: str) -> Dict[str, Any]:
        """查询任务结果"""
        return self._request("GET", f"/api/result/{task_id}")

    def wait_for_result(self, task_id: str, max_retries: int = 60, interval: float = 3.0) -> Optional[str]:
        """轮询等待任务完成，返回图片 URL"""
        for i in range(max_retries):
            result = self.query_result(task_id)
            status = result.get("status")

            if status == "success":
                return result.get("result_url")
            elif status == "failed":
                error = result.get("error_message", "生成失败")
                raise SelfPhotoAPIError(f"生成失败: {error}")

            time.sleep(interval)

        raise SelfPhotoAPIError("轮询超时")

    def update_reply(self, task_id: str, reply: str) -> Dict[str, Any]:
        """更新图片的回复配文"""
        return self._request("POST", f"/api/gallery/reply?task_id={task_id}", {"reply": reply})

    def get_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取对话历史"""
        result = self._request("GET", f"/api/conversations?limit={limit}")
        return result.get("conversations", [])

    def save_conversation(self, role: str, content: str, generation_id: int = None) -> Dict[str, Any]:
        """保存对话记录"""
        data = {
            "role": role,
            "content": content
        }
        if generation_id:
            data["generation_id"] = generation_id
        return self._request("POST", "/api/conversations", data)


def test_api():
    """测试 API 连接"""
    import sys

    if len(sys.argv) < 2:
        api_key = "sp_bb55942ef62f4d51993baafd"  # 测试用
    else:
        api_key = sys.argv[1]

    client = SelfPhotoClient(api_key)

    print("=== 1. 检查余额 ===")
    balance = client.check_balance()
    print(f"剩余额度: {balance.get('remaining_total')}")

    print("\n=== 2. 获取用户信息 ===")
    user = client.get_user_info()
    ref_image = user.get("reference_image")
    print(f"参考图: {ref_image}")

    if not ref_image:
        print("错误：未设置参考图")
        return

    print("\n=== 3. 生成图片 ===")
    # 将 /static/uploads/3/xxx.jpg 转换为 uploads/3/xxx.jpg
    image_path = ref_image.replace("/static/", "")
    result = client.generate(
        prompt="甜美少女风格，户外阳光照耀，微笑",
        image_filename=image_path
    )
    print(f"任务ID: {result.get('task_id')}")

    print("\n=== 4. 等待生成完成 ===")
    image_url = client.wait_for_result(result["task_id"])
    print(f"图片URL: {image_url}")
    print("\n✅ 测试成功!")


if __name__ == "__main__":
    test_api()
