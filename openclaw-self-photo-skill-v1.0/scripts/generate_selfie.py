#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self Photo Skill v2.1 - 直接调用 Self Photo API
支持角色自定义、情感记忆、场景生成
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from api_client import SelfPhotoClient, SelfPhotoAPIError
from time_context import get_time_context, build_prompt, should_trigger


# 飞书配置
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_USER_OPEN_ID = os.environ.get("FEISHU_USER_OPEN_ID", "")  # OpenClaw 传入的用户 Open ID

# 缓存 token 文件
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".feishu_token_cache.json")

# 本地存储上次的参考图时间戳
CACHE_FILE = os.path.join(os.path.dirname(__file__), ".reference_cache.json")

# API Key 缓存文件 (P0-1 修复)
API_KEY_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".api_key_cache.json")


def get_api_key() -> str:
    """获取 API Key：优先从环境变量，其次从缓存文件"""
    # 先从环境变量读取
    api_key = os.environ.get("SELF_PHOTO_API_KEY")
    if api_key:
        return api_key

    # 再从缓存文件读取
    if os.path.exists(API_KEY_CACHE_FILE):
        try:
            with open(API_KEY_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                return cache.get("api_key")
        except:
            pass

    return None


def save_api_key(api_key: str):
    """保存 API Key 到缓存文件"""
    try:
        with open(API_KEY_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({"api_key": api_key}, f)
    except:
        pass


def get_feishu_token() -> str:
    """获取飞书 tenant_access_token"""
    global FEISHU_APP_ID, FEISHU_APP_SECRET

    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        print("未配置飞书 APP_ID 或 APP_SECRET", file=sys.stderr)
        return None

    # 检查缓存
    try:
        if os.path.exists(TOKEN_CACHE_FILE):
            with open(TOKEN_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                # 提前 5 分钟过期
                if cache.get("expires_at", 0) > time.time() + 300:
                    return cache.get("token")
    except:
        pass

    # 获取新 token
    try:
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        data = {
            "app_id": FEISHU_APP_ID,
            "app_secret": FEISHU_APP_SECRET
        }

        response = requests.post(url, headers=headers, json=data, timeout=10)
        result = response.json()

        print(f"获取 token 响应: {result}", file=sys.stderr)

        if result.get("code") == 0:
            token = result.get("data", {}).get("tenant_access_token")
            expires_in = result.get("data", {}).get("expires_in", 7200)

            # 缓存 token
            with open(TOKEN_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "token": token,
                    "expires_at": time.time() + expires_in
                }, f)

            return token
        else:
            print(f"获取 token 失败: {result.get('msg')}", file=sys.stderr)
            return None

    except Exception as e:
        print(f"获取 token 异常: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None


def load_cached_reference_time() -> str:
    """加载缓存的参考图更新时间"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("reference_image_updated_at")
    except:
        pass
    return None


def save_cached_reference_time(updated_at: str):
    """保存参考图更新时间到缓存"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({"reference_image_updated_at": updated_at}, f)
    except:
        pass


def check_reference_image_changed(user_info: dict) -> bool:
    """检查参考图是否发生变化"""
    current_updated_at = user_info.get("reference_image_updated_at")
    cached_updated_at = load_cached_reference_time()

    if not current_updated_at:
        return False

    # 如果没有缓存，说明是首次
    if not cached_updated_at:
        save_cached_reference_time(current_updated_at)
        return False

    # 比较时间戳
    if current_updated_at != cached_updated_at:
        save_cached_reference_time(current_updated_at)
        return True

    return False


def upload_image_to_feishu(image_url: str) -> str:
    """下载图片并上传到飞书，返回 image_key"""
    # 获取 token
    token = get_feishu_token()
    if not token:
        print("无法获取飞书 token", file=sys.stderr)
        return None

    try:
        # 下载图片
        print(f"下载图片: {image_url}", file=sys.stderr)
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        # 获取文件扩展名
        content_type = response.headers.get("Content-Type", "")
        ext = "jpg"
        if "png" in content_type:
            ext = "png"

        # 生成文件名
        filename = f"selfie_{int(time.time())}.{ext}"

        # 上传到飞书
        print(f"上传到飞书: {filename}", file=sys.stderr)

        url = "https://open.feishu.cn/open-apis/im/v1/images"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        files = {
            'image': (filename, response.content),
            'image_type': (None, 'message')
        }

        upload_response = requests.post(url, files=files, headers=headers, timeout=60)

        print(f"飞书上传响应: {upload_response.text}", file=sys.stderr)

        result = upload_response.json()

        if result.get("code") == 0:
            image_key = result.get("data", {}).get("image_key")
            print(f"图片上传飞书成功: {image_key}", file=sys.stderr)
            return image_key
        else:
            print(f"上传飞书失败: {result.get('msg')}", file=sys.stderr)
            # 如果是 token 过期，删除缓存重试
            if result.get("code") == 99991663:  # token 过期
                try:
                    os.remove(TOKEN_CACHE_FILE)
                except:
                    pass
            return None

    except Exception as e:
        print(f"上传飞书异常: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None


def send_feishu_image_message(image_key: str, reply_text: str = "") -> bool:
    """
    通过飞书 API 直接发送图片消息给用户
    需要 FEISHU_USER_OPEN_ID 环境变量（OpenClaw 传入）

    参数：
        image_key: upload_image_to_feishu 返回的 image_key
        reply_text: 随图片发送的文字（可选，图片消息会单独发一条）

    返回：是否发送成功
    """
    if not image_key:
        return False

    open_id = FEISHU_USER_OPEN_ID
    if not open_id:
        print("无法发送飞书图片消息：缺少用户 Open ID（FEISHU_USER_OPEN_ID 未设置）", file=sys.stderr)
        return False

    token = get_feishu_token()
    if not token:
        print("无法发送飞书图片消息：无法获取 token", file=sys.stderr)
        return False

    try:
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # 先发文字消息
        if reply_text:
            text_payload = {
                "receive_id": open_id,
                "msg_type": "text",
                "content": json.dumps({"text": reply_text})
            }
            text_resp = requests.post(url, headers=headers, json=text_payload, timeout=10)
            text_result = text_resp.json()
            if text_result.get("code") == 0:
                print(f"飞书文字消息发送成功: {text_result.get('data', {}).get('message_id')}", file=sys.stderr)
            else:
                print(f"飞书文字消息发送失败: {text_result.get('msg')}", file=sys.stderr)

        # 发图片消息
        msg_payload = {
            "receive_id": open_id,
            "msg_type": "image",
            "content": json.dumps({"image_key": image_key})
        }
        img_resp = requests.post(url, headers=headers, json=msg_payload, timeout=10)
        img_result = img_resp.json()

        if img_result.get("code") == 0:
            msg_id = img_result.get("data", {}).get("message_id")
            print(f"飞书图片消息发送成功: {msg_id}", file=sys.stderr)
            return True
        else:
            print(f"飞书图片消息发送失败: {img_result.get('msg')}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"飞书图片消息发送异常: {e}", file=sys.stderr)
        return False


def get_waiting_reply(user_input: str) -> str:
    """根据用户输入获取等待回复语（简短自然）"""
    replies = [
        "好滴，等我一下~",
        "马上来",
        "来啦",
        "稍等哦",
        "好嘞",
    ]
    return replies[int(time.time()) % len(replies)]


def build_reply_with_personality(context: Dict, role_nickname: str = "", role_zodiac: str = "", role_catchphrase: str = "", role_personality: str = "") -> str:
    """
    根据人物设定构建回复文案，融入性格、星座、口头禅

    Args:
        context: 场景上下文，包含 reply 字段
        role_nickname: 角色昵称
        role_zodiac: 星座
        role_catchphrase: 口头禅
        role_personality: 性格描述

    Returns:
        个性化的回复文案
    """
    # 获取基础回复
    base_reply = context.get("reply", "给你拍一张~")

    # 如果有口头禅，融入到回复中
    if role_catchphrase and role_catchphrase not in base_reply:
        # 在回复末尾或开头添加口头禅
        if "～" in base_reply or "~" in base_reply:
            base_reply = base_reply.replace("～", f"～{role_catchphrase} ").replace("~", f"~{role_catchphrase} ")
        else:
            base_reply = f"{role_catchphrase} {base_reply}"

    # 如果有星座，可以添加一些星座相关的语气
    zodiac_moods = {
        "白羊座": "充满活力的",
        "金牛座": "稳重的",
        "双子座": "古灵精怪的",
        "巨蟹座": "温柔的",
        "狮子座": "自信的",
        "处女座": "细腻的",
        "天秤座": "优雅的",
        "天蝎座": "神秘的",
        "射手座": "乐观的",
        "摩羯座": "成熟的",
        "水瓶座": "特别的",
        "双鱼座": "浪漫的"
    }

    zodiac_mood = ""
    for sign, mood in zodiac_moods.items():
        if sign in role_zodiac:
            zodiac_mood = mood
            break

    # 如果有性格描述，融入回复
    if role_personality:
        # 性格关键词映射
        personality_keywords = {
            "温柔": "温柔的",
            "体贴": "体贴的",
            "傲娇": "小傲娇的",
            "可爱": "可爱的",
            "活泼": "活泼的",
            "文静": "文静的",
            "御姐": "成熟魅力的",
            "萌": "萌萌的",
            "甜": "甜甜的",
            "酷": "酷酷的",
            "痞": "痞痞的",
        }

        personality_prefix = ""
        for kw, prefix in personality_keywords.items():
            if kw in role_personality:
                personality_prefix = prefix
                break

    # 构建个性化回复
    reply_parts = []

    # 添加昵称
    if role_nickname:
        # 根据性格选择不同的称呼方式
        if "傲娇" in role_personality:
            reply_parts.append(f"哼，{role_nickname}我来啦～")
        elif "可爱" in role_personality or "萌" in role_personality:
            reply_parts.append(f"{role_nickname}来啦～")
        else:
            reply_parts.append(base_reply)
    else:
        reply_parts.append(base_reply)

    final_reply = " ".join(reply_parts) if reply_parts else base_reply

    return final_reply


def main():
    """主入口"""
    if len(sys.argv) < 2:
        print("Usage: python3 generate_selfie.py <user_input> [current_time] [conversations_json]", file=sys.stderr)
        sys.exit(1)

    user_input = sys.argv[1]
    current_time = sys.argv[2] if len(sys.argv) > 2 else None
    conversations_json = sys.argv[3] if len(sys.argv) > 3 else None

    # 解析对话历史
    conversations = None
    if conversations_json:
        try:
            conversations = json.loads(conversations_json)
            print(f"接收到对话历史: {len(conversations)} 条", file=sys.stderr)
        except Exception as e:
            print(f"解析对话历史失败: {e}", file=sys.stderr)
    else:
        print("未收到对话历史参数", file=sys.stderr)

    # 1. 检查是否应该触发
    if not should_trigger(user_input):
        print("NO_TRIGGER")
        sys.exit(0)

    # 2. 获取配置
    api_key = get_api_key()
    api_url = os.environ.get("SELF_PHOTO_API_URL", "http://localhost:8002")

    if not api_key:
        print("ERROR: 未配置 SELF_PHOTO_API_KEY", file=sys.stderr)
        print("请设置环境变量：export SELF_PHOTO_API_KEY=sp_xxx...", file=sys.stderr)
        print("或者在平台获取 API Key 后配置", file=sys.stderr)
        sys.exit(1)

    # 缓存 API Key 以便下次使用
    save_api_key(api_key)

    # 3. 先输出等待消息（立即回复用户）
    waiting_reply = get_waiting_reply(user_input)

    # 输出等待消息到 stdout（让 OpenClaw 立即发送等待消息）
    # 使用特定格式让 OpenClaw 识别
    print(f"REPLY_FIRST:{waiting_reply}", file=sys.stdout)
    sys.stdout.flush()

    # 4. 初始化客户端
    try:
        client = SelfPhotoClient(api_key, api_url)
    except SelfPhotoAPIError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # 5. 检查参考图是否变化，获取人物设定
    try:
        user_info = client.get_user_info()
        ref_image = user_info.get("reference_image")
        ref_updated_at = user_info.get("reference_image_updated_at")

        print(f"原始参考图URL: {ref_image}", file=sys.stderr)

        # 获取人物设定
        role_nickname = user_info.get("role_nickname") or ""
        role_personality = user_info.get("role_personality") or ""
        role_age = user_info.get("role_age") or ""
        role_zodiac = user_info.get("role_zodiac") or ""
        role_profession = user_info.get("role_profession") or ""
        role_catchphrase = user_info.get("role_catchphrase") or ""

        # 保存人物设定到环境变量，供后续使用
        if role_nickname:
            os.environ["ROLE_NAME"] = role_nickname
        if role_personality:
            os.environ["ROLE_PERSONALITY"] = role_personality
        if role_age:
            os.environ["ROLE_AGE"] = role_age
        if role_zodiac:
            os.environ["ROLE_ZODIAC"] = role_zodiac
        if role_profession:
            os.environ["ROLE_PROFESSION"] = role_profession
        if role_catchphrase:
            os.environ["ROLE_CATCHPHRASE"] = role_catchphrase

        print(f"角色设定: {role_nickname}, {role_age}岁, {role_profession}", file=sys.stderr)
        print(f"性格: {role_personality}", file=sys.stderr)

        if not ref_image:
            print("ERROR: 未设置参考图，请在平台选择参考图", file=sys.stderr)
            sys.exit(1)

        # 检查参考图是否变化
        image_changed = check_reference_image_changed(user_info)
        if image_changed:
            print("检测到参考图已更新！", file=sys.stderr)
            # 输出参考图变化的消息
            print(f"REFERENCE_CHANGED:{ref_image}", file=sys.stderr)

    except SelfPhotoAPIError as e:
        print(f"ERROR: 获取用户信息失败 - {e}", file=sys.stderr)
        sys.exit(1)

    # ===== Skill 端自己获取对话历史 =====
    # 1. 先保存当前用户输入作为对话（即使余额不足也保存）
    debug_file = os.path.join(os.path.dirname(__file__), "debug.log")
    with open(debug_file, "a", encoding="utf-8") as f:
        f.write(f"DEBUG: 开始保存对话, user_input={user_input}\n")

    try:
        result = client.save_conversation(role="user", content=user_input)
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write(f"已保存用户对话: {result}\n")
    except Exception as e:
        import traceback
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write(f"保存用户对话失败: {e}\n")
            traceback.print_exc(file=f)

    # 2. 获取最近的对话历史（从服务端）
    try:
        recent_convos = client.get_conversations(limit=5)
        print(f"获取到对话: {recent_convos}", file=sys.stderr)
        # 转换为 API 需要的格式
        conversations_from_api = [{"role": c["role"], "content": c["content"]} for c in recent_convos]
        print(f"获取到 {len(conversations_from_api)} 条对话历史", file=sys.stderr)
    except Exception as e:
        import traceback
        print(f"获取对话历史失败: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        conversations_from_api = []

    # 6. 检查余额
    try:
        balance = client.check_balance()
        remaining = balance.get("remaining_total", 0)
        if remaining <= 0:
            print("ERROR: 积分不足", file=sys.stderr)
            print("请前往平台充值", file=sys.stderr)
            sys.exit(1)
        print(f"剩余积分: {remaining}", file=sys.stderr)
    except SelfPhotoAPIError as e:
        print(f"ERROR: 检查余额失败 - {e}", file=sys.stderr)
        sys.exit(1)

    # 7. 获取时间场景
    context = get_time_context(current_time, user_input)
    scene_prompt = build_prompt(context)

    # 8. 解析用户输入中的风格 (P2扩展)
    user_style = ""
    style_keywords = {
        "职场": "商务正装，西装外套",
        "商务": "职业装，白衬衫",
        "休闲": "休闲装，舒适穿搭",
        "运动": "运动服，健身装",
        "健身": "健身服，运动内衣",
        "甜美": "甜美风格，公主裙",
        "可爱": "可爱风格，洛丽塔",
        "jk": "JK制服，百褶裙",
        "Lolita": "洛丽塔裙装，甜美系",
        "泳装": "泳装，比基尼",
        "海边": "度假风格，泳装",
        "潮酷": "潮酷风格，街头风",
        "酷": "酷girl风格，黑色系",
        "复古": "复古风格，港风",
        "校园": "校园风格，校服",
        "学生": "学生装，背带裤",
        "旗袍": "旗袍，中国风",
        "汉服": "汉服，古风",
        "和服": "和服，浴衣",
        "制服": "制服，空姐装",
    }

    for keyword, style in style_keywords.items():
        if keyword in user_input:
            user_style = style
            break

    # 构建最终 Prompt
    if user_style:
        final_prompt = f"{scene_prompt}，{user_style}。"
    else:
        final_prompt = scene_prompt

    print(f"场景: {context.get('scene', '默认场景')}", file=sys.stderr)
    print(f"Prompt: {final_prompt}", file=sys.stderr)

    # 9. 调用生成 API
    # 处理参考图路径，去掉 /static/ 前缀
    image_path = ref_image
    if image_path.startswith("/static/"):
        image_path = image_path.replace("/static/", "")
    elif image_path.startswith("http"):
        # 如果是完整URL，提取路径部分
        import urllib.parse
        parsed = urllib.parse.urlparse(image_path)
        image_path = parsed.path
        if image_path.startswith("/"):
            image_path = image_path[1:]

    print(f"处理后的图片路径: {image_path}", file=sys.stderr)

    # 优先使用 API 获取的对话
    final_conversations = conversations_from_api if conversations_from_api else (conversations or [])

    try:
        print("正在生成图片...", file=sys.stderr)
        result = client.generate(
            prompt=final_prompt,
            image_filename=image_path,
            aspect_ratio="9:16",
            resolution="1k",
            user_input=user_input,  # 传入用户原始对话
            conversations=final_conversations,  # 传入对话历史
            role_nickname=role_nickname  # 传入角色昵称
        )
        task_id = result.get("task_id")
        print(f"任务ID: {task_id}", file=sys.stderr)
    except SelfPhotoAPIError as e:
        print(f"ERROR: 生成失败 - {e}", file=sys.stderr)
        sys.exit(1)

    # 10. 轮询等待结果
    try:
        print("等待生成完成...", file=sys.stderr)
        image_url = client.wait_for_result(task_id, max_retries=60, interval=3.0)
        print(f"图片生成成功: {image_url}", file=sys.stderr)
    except SelfPhotoAPIError as e:
        print(f"ERROR: 获取结果失败 - {e}", file=sys.stderr)
        sys.exit(1)

    # 11. 上传到飞书
    feishu_configured = bool(FEISHU_APP_ID and FEISHU_APP_SECRET)
    image_key = upload_image_to_feishu(image_url) if feishu_configured else None

    # 12. 获取剩余积分
    try:
        balance = client.check_balance()
        remaining = balance.get("remaining_total", 0)
    except:
        remaining = "未知"

    # 13. 生成回复文案（只在没有飞书图片时使用）
    base_reply = context.get("reply", "给你拍一张~")

    # 构建个性化回复（融入性格、星座、口头禅）
    final_reply = build_reply_with_personality(
        context=context,
        role_nickname=role_nickname,
        role_zodiac=role_zodiac,
        role_catchphrase=role_catchphrase,
        role_personality=role_personality
    )

    # 只有明确知道飞书未配置时，才添加提示
    if not feishu_configured:
        tip = " [提示：提供飞书 APP_ID 和 APP_SECRET 可以直接发图片，体验更好哦]"
        base_reply = final_reply + tip
    else:
        base_reply = final_reply

    # 14. 保存回复配文到后端（保存不含飞书提示的核心回复）
    try:
        client.update_reply(task_id, final_reply)
        print(f"已保存回复配文: {final_reply}", file=sys.stderr)
    except Exception as e:
        print(f"保存回复配文失败: {e}", file=sys.stderr)

    # 15. 保存 AI 回复作为对话记录
    try:
        client.save_conversation(role="assistant", content=final_reply)
        print(f"已保存 AI 对话", file=sys.stderr)
    except Exception as e:
        print(f"保存 AI 对话失败: {e}", file=sys.stderr)

    # 15. 输出最终结果
    # 优先使用图片链接（用户可直接点击查看）
    # 如果飞书凭证完整（APP_ID + APP_SECRET + USER_OPEN_ID），OpenClaw 收到 FEISHU_IMAGE: 前缀后，
    # 会调用飞书 API 直接发图片消息给用户（而非发链接）
    reply_text = base_reply
    if image_url:
        encoded_url = image_url.replace('_', '%5F')
        reply_text = f"{reply_text}\n📷 {encoded_url}"

    # 飞书凭证完整时，输出特殊格式让 OpenClaw 识别并发送图片
    feishu_can_send_image = bool(FEISHU_APP_ID and FEISHU_APP_SECRET and FEISHU_USER_OPEN_ID and image_key)
    if feishu_can_send_image:
        # OpenClaw 收到此格式后，解析 image_key 并通过飞书 API 发图片给用户
        # 格式：FEISHU_IMAGE:<image_key>:FEISHU_IMAGE_END:<回复文字>
        # 注意：OpenClaw 发完图片后，应只发送 <回复文字> 部分作为文字消息
        print(f"FEISHU_IMAGE:{image_key}:FEISHU_IMAGE_END:{reply_text}")
    else:
        print(reply_text)


if __name__ == "__main__":
    # 设置 UTF-8 编码，解决 Windows 控制台输出问题
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    main()
