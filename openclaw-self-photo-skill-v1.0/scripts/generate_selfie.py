#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self Photo Skill v1.1 - 主脚本

职责：
1. 获取用户输入
2. 调用服务器 API 获取场景（服务端处理场景生成）
3. 调用服务器 API 生成图片
4. 发送图片和回复（支持飞书直接发图片）

注意：所有提示词逻辑都在服务器端，Skill 只负责调用流程
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
import urllib.parse
import uuid

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from api_client import SelfPhotoClient, SelfPhotoAPIError


# ==================== 飞书 API ====================

def get_feishu_token(app_id: str, app_secret: str) -> str:
    """获取飞书 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if result.get("code") != 0:
        raise Exception(f"获取飞书token失败: {result}")
    return result["tenant_access_token"]


def upload_image_to_feishu(token: str, image_data: bytes) -> str:
    """上传图片到飞书，返回 image_key"""
    boundary = str(uuid.uuid4())
    body = (
        b"--" + boundary.encode() + b"\r\n"
        b'Content-Disposition: form-data; name="image_type"\r\n\r\n'
        b"message\r\n"
        b"--" + boundary.encode() + b"\r\n"
        b'Content-Disposition: form-data; name="image"; filename="selfie.jpg"\r\n'
        b"Content-Type: application/octet-stream\r\n\r\n"
    ) + image_data + b"\r\n" + (
        b"--" + boundary.encode() + b"--\r\n"
    )
    url = "https://open.feishu.cn/open-apis/im/v1/images"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if result.get("code") != 0:
        raise Exception(f"上传飞书图片失败: code={result.get('code')}, msg={result.get('msg')}")
    return result["data"]["image_key"]


def send_feishu_image(token: str, receive_id: str, image_key: str, reply: str) -> None:
    """通过飞书机器人发送图片消息"""
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    payload = {
        "receive_id": receive_id,
        "msg_type": "image",
        "content": json.dumps({"image_key": image_key}),
        "uuid": str(uuid.uuid4())
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if result.get("code") != 0:
        print(f"[WARN] 飞书发图片失败: {result}", file=sys.stderr)

    # 再发一条文字消息
    payload["msg_type"] = "text"
    payload["content"] = json.dumps({"text": reply})
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if result.get("code") != 0:
        print(f"[WARN] 飞书发文字失败: {result}", file=sys.stderr)


def download_image(url: str) -> bytes:
    """下载图片数据"""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def try_send_feishu(image_url: str, reply: str, feishu_app_id: str, feishu_app_secret: str, feishu_chat_id: str) -> bool:
    """尝试通过飞书发图片，如果成功返回 True"""
    if not all([feishu_app_id, feishu_app_secret, feishu_chat_id]):
        return False
    try:
        token = get_feishu_token(feishu_app_id, feishu_app_secret)
        image_data = download_image(image_url)
        image_key = upload_image_to_feishu(token, image_data)
        send_feishu_image(token, feishu_chat_id, image_key, reply)
        return True
    except Exception as e:
        print(f"[WARN] 飞书发图片失败，降级为链接: {e}", file=sys.stderr)
        return False


def main():
    """主入口"""
    if len(sys.argv) < 2:
        print("Usage: python3 generate_selfie.py <user_input> [current_time]", file=sys.stderr)
        sys.exit(1)

    user_input = sys.argv[1]
    current_time = sys.argv[2] if len(sys.argv) > 2 else None

    # 1. 获取 API Key
    api_key = os.environ.get("SELF_PHOTO_API_KEY")
    api_url = os.environ.get("SELF_PHOTO_API_URL", "http://47.110.145.186:8002")

    if not api_key:
        print("ERROR: 未配置 SELF_PHOTO_API_KEY", file=sys.stderr)
        sys.exit(1)

    # 2. 初始化客户端
    try:
        client = SelfPhotoClient(api_key, api_url)
    except SelfPhotoAPIError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. 发送等待消息
    waiting_replies = ["好滴，等我一下~", "马上来", "来啦", "稍等哦"]
    waiting_reply = waiting_replies[int(time.time()) % len(waiting_replies)]
    print(f"REPLY_FIRST:{waiting_reply}", file=sys.stdout)
    sys.stdout.flush()

    # 4. 获取用户信息（包括参考图）
    try:
        user_info = client.get_user_info()
        ref_image = user_info.get("reference_image")
        role_nickname = user_info.get("role_nickname", "")

        if not ref_image:
            print("ERROR: 请先上传参考图", file=sys.stderr)
            sys.exit(1)
    except SelfPhotoAPIError as e:
        print(f"ERROR: 获取用户信息失败 - {e}", file=sys.stderr)
        sys.exit(1)

    # 5. 检查积分
    try:
        balance = client.check_balance()
        remaining = balance.get("remaining_total", 0)
        if remaining <= 0:
            print("ERROR: 积分不足", file=sys.stderr)
            sys.exit(1)
    except SelfPhotoAPIError as e:
        print(f"ERROR: 检查积分失败 - {e}", file=sys.stderr)

    # 6. 调用服务端 API 获取场景（场景生成在服务端完成）
    # 服务端返回：scene, prompt, reply 等
    try:
        scene_url = f"{api_url}/api/scene"

        params = {"user_input": user_input}
        if current_time:
            params["current_time"] = current_time

        url = f"{scene_url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(req, timeout=30) as response:
            scene_data = json.loads(response.read().decode("utf-8"))

        if not scene_data.get("should_trigger"):
            print("NO_TRIGGER", file=sys.stderr)
            sys.exit(0)

        # 获取服务端返回的 prompt 和 reply
        prompt = scene_data.get("prompt", "")
        reply = scene_data.get("reply", "给你拍一张~")
        scene_name = scene_data.get("scene", "默认场景")

        print(f"场景: {scene_name}", file=sys.stderr)
        print(f"回复: {reply}", file=sys.stderr)

    except Exception as e:
        print(f"ERROR: 获取场景失败 - {e}", file=sys.stderr)
        raise

    # 7. 处理参考图路径
    image_path = ref_image
    if image_path.startswith("/static/"):
        image_path = image_path.replace("/static/", "")
    elif image_path.startswith("http"):
        parsed = urllib.parse.urlparse(image_path)
        image_path = parsed.path
        if image_path.startswith("/"):
            image_path = image_path[1:]

    # 8. 生成图片
    try:
        print("正在生成图片...", file=sys.stderr)
        result = client.generate(
            prompt=prompt,
            image_filename=image_path,
            aspect_ratio="9:16",
            resolution="1k",
            user_input=user_input,
            role_nickname=role_nickname
        )
        task_id = result.get("task_id")
        print(f"任务ID: {task_id}", file=sys.stderr)
    except SelfPhotoAPIError as e:
        print(f"ERROR: 生成失败 - {e}", file=sys.stderr)
        sys.exit(1)

    # 9. 轮询等待结果
    try:
        print("等待生成完成...", file=sys.stderr)
        image_url = client.wait_for_result(task_id, max_retries=60, interval=3.0)
        print(f"图片生成成功: {image_url}", file=sys.stderr)
    except SelfPhotoAPIError as e:
        print(f"ERROR: 获取结果失败 - {e}", file=sys.stderr)
        sys.exit(1)

    # 10. 保存回复到服务器
    try:
        client.update_reply(task_id, reply)
        print(f"已保存回复: {reply}", file=sys.stderr)
    except Exception as e:
        raise Exception(f"保存回复失败: {e}")

    # 11. 保存对话记录
    try:
        generation_id = result.get("generation_id")
        if generation_id:
            # 保存用户的消息
            client.save_conversation("user", user_input, generation_id)
            # 保存AI的回复
            client.save_conversation("assistant", reply, generation_id)
            print(f"已保存对话记录: user_input={user_input[:20]}..., reply={reply[:20]}..., generation_id={generation_id}", file=sys.stderr)
        else:
            print(f"未获取到generation_id，无法保存对话", file=sys.stderr)
    except Exception as e:
        raise Exception(f"保存对话失败: {e}")

    # 12. 输出最终结果
    # 优先尝试通过飞书直接发图片（需要配置飞书凭证）
    feishu_app_id = os.environ.get("FEISHU_APP_ID", "")
    feishu_app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    feishu_chat_id = os.environ.get("FEISHU_CHAT_ID", "")

    if all([feishu_app_id, feishu_app_secret, feishu_chat_id]):
        sent = try_send_feishu(image_url, reply, feishu_app_id, feishu_app_secret, feishu_chat_id)
        if sent:
            # 飞书已发送，stdout 输出简短标记让 OpenClaw 知道已完成
            print(f"[OK] 已通过飞书发送图片和回复")
        else:
            # 降级为链接
            print(f"FINAL_REPLY:{reply}\n{image_url}")
    else:
        # 未配置飞书凭证，输出链接
        print(f"FINAL_REPLY:{reply}\n{image_url}")


if __name__ == "__main__":
    main()
