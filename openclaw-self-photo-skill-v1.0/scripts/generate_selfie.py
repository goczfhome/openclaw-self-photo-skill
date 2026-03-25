#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self Photo Skill v1.0 - 主脚本

职责：
1. 获取用户输入
2. 调用服务器 API 获取场景（服务端处理场景生成）
3. 调用服务器 API 生成图片
4. 发送图片和回复

注意：所有提示词逻辑都在服务器端，Skill 只负责调用流程
"""

import os
import sys
import time
import json

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from api_client import SelfPhotoClient, SelfPhotoAPIError


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
        import urllib.request
        import urllib.parse

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
        # 备用：使用默认提示词
        prompt = "甜美少女风格"
        reply = "给你拍一张~"

    # 7. 处理参考图路径
    image_path = ref_image
    if image_path.startswith("/static/"):
        image_path = image_path.replace("/static/", "")
    elif image_path.startswith("http"):
        import urllib.parse
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
        print(f"保存回复失败: {e}", file=sys.stderr)

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
        print(f"保存对话失败: {e}", file=sys.stderr)

    # 11. 输出最终结果
    # 飞书发送图片 + 文字
    final_output = f"FINAL_REPLY:{reply}\n{image_url}"
    print(final_output)


if __name__ == "__main__":
    main()
