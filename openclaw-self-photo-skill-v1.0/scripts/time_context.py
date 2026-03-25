#!/usr/bin/env python3
"""
时间场景生成器
根据当前时间生成合适的场景描述
"""

import os
import random
from datetime import datetime
from typing import Dict, Any


def get_time_context(current_time_str: str = None, user_input: str = None) -> Dict[str, str]:
    """
    根据当前时间智能匹配场景（随机选择）
    支持问候场景和情绪场景（P1-2）

    Args:
        current_time_str: 时间字符串 (HH:MM)，默认为当前时间
        user_input: 用户输入文本，用于识别情绪和问候

    Returns:
        包含场景信息的字典
    """
    if current_time_str:
        try:
            now = datetime.strptime(current_time_str, "%H:%M")
        except ValueError:
            now = datetime.now()
    else:
        now = datetime.now()

    hour = now.hour
    user_input_lower = user_input.lower() if user_input else ""

    # ===== P1-2: 问候场景处理 =====
    # 早安场景
    if any(kw in user_input_lower for kw in ["早啊", "早安", "早上好", "おはよう", "good morning"]):
        return {
            "scene": "清晨起床",
            "outfit": "可爱卡通睡衣",
            "light": "清晨阳光从窗帘透进，柔和温暖",
            "expression": "刚睡醒的慵懒笑容",
            "action": "坐床上伸懒腰",
            "location": "卧室床上",
            "reply": "早安呀🌅！新的一天开始了～你吃早餐了吗？",
            "time_label": "早晨"
        }

    # 晚安场景
    if any(kw in user_input_lower for kw in ["晚安", "睡了", "晚好", "おやすみ", "good night"]):
        return {
            "scene": "准备睡觉",
            "outfit": "柔软家居睡衣",
            "light": "温馨床头灯，昏暗柔和",
            "expression": "困倦但温柔的微笑",
            "action": "躺床上盖被子",
            "location": "卧室床上",
            "reply": "晚安🌙！好梦～你也早点睡哦！",
            "time_label": "深夜"
        }

    # ===== P1-2: 情绪场景处理 =====
    # 想你了场景
    if any(kw in user_input_lower for kw in ["想你了", "好想你", "想你想", "miss you"]):
        return {
            "scene": "惊喜自拍",
            "outfit": "精心打扮的漂亮裙子",
            "light": "明亮温暖的室内光",
            "expression": "惊喜又开心的笑容",
            "action": "双手捧脸对镜自拍",
            "location": "客厅全身镜前",
            "reply": "我也想你啦！😘 给你比心～今天过得怎么样？",
            "time_label": "互动"
        }

    # 累了/心情不好场景
    if any(kw in user_input_lower for kw in ["好累", "累死了", "今天好累", "心情不好", "不爽", "郁闷", "难过"]):
        return {
            "scene": "安慰自拍",
            "outfit": "舒适居家服",
            "light": "柔和暖光",
            "expression": "心疼的温柔表情",
            "action": "对着镜子做加油手势",
            "location": "卧室镜子前",
            "reply": "辛苦啦💪！抱抱～坚强！ todo good day 会好起来的！",
            "time_label": "互动"
        }

    # 吃饭相关场景
    if any(kw in user_input_lower for kw in ["吃饭了吗", "吃了吗", "吃什么", "我吃了", "吃过了"]):
        return {
            "scene": "用餐",
            "outfit": "舒适休闲装",
            "light": "餐厅暖光，食欲感",
            "expression": "满足的笑容",
            "action": "举着筷子或勺子",
            "location": "餐桌前",
            "reply": "正在吃呀🍚～你吃的啥呀？",
            "time_label": "中午"
        }

    # 时间段场景库（每个时段3-5个场景，带反问句激发对话）
    contexts = {
        # 早晨 (6-9点)
        (6, 9): [
            {
                "scene": "刚起床，在家吃早餐",
                "outfit": "宽松睡衣，头发微乱",
                "light": "清晨柔和自然光，窗帘透光，暖色调",
                "expression": "睡眼惺忪",
                "action": "举着吐司面包",
                "location": "家里餐厅",
                "reply": "刚醒，在吃早餐🍞，你吃了没？",
                "time_label": "早晨"
            },
            {
                "scene": "卫生间洗漱",
                "outfit": "毛绒睡衣",
                "light": "浴室明亮灯光，镜子反光",
                "expression": "睡醒后清醒中",
                "action": "拿着牙刷刷牙",
                "location": "卫生间",
                "reply": "刚起床，在刷牙🪥，你咋这么早？",
                "time_label": "早晨"
            },
            {
                "scene": "阳台晒太阳",
                "outfit": "居家休闲服",
                "light": "晨光温柔，阳光斜射",
                "expression": "享受阳光",
                "action": "双手搭着栏杆",
                "location": "自家阳台",
                "reply": "阳台晒太阳☀️，你吃早餐了吗？",
                "time_label": "早晨"
            },
            {
                "scene": "厨房准备早餐",
                "outfit": "卡通睡衣",
                "light": "厨房灯光，窗外天亮",
                "expression": "认真做饭",
                "action": "煎鸡蛋",
                "location": "家里厨房",
                "reply": "在做早餐🍳，你要来一份吗？",
                "time_label": "早晨"
            },
            {
                "scene": "化妆打扮",
                "outfit": "穿着内衣或吊带",
                "light": "化妆镜灯光，柔和明亮",
                "expression": "专注",
                "action": "对着镜子化妆",
                "location": "梳妆台",
                "reply": "化个妆💄，你今天有啥安排？",
                "time_label": "早晨"
            }
        ],
        # 上午 (9-12点)
        (9, 12): [
            {
                "scene": "在单位/公司工作",
                "outfit": "简约白T恤配牛仔裤",
                "light": "办公室明亮灯光，屏幕反光，冷白光",
                "expression": "专注中带着一丝摸鱼的轻松",
                "action": "对着电脑屏幕",
                "location": "办公室工位",
                "reply": "上班中💻，摸鱼时间到～你呢？",
                "time_label": "上午"
            },
            {
                "scene": "会议室开会",
                "outfit": "职业装，白衬衫",
                "light": "会议室荧光灯，明亮",
                "expression": "认真听讲",
                "action": "抱着笔记本",
                "location": "公司会议室",
                "reply": "开会中😴，好困啊～你们呢？",
                "time_label": "上午"
            },
            {
                "scene": "在公司茶水间",
                "outfit": "职业休闲装",
                "light": "茶水间柔和灯光",
                "expression": "放松",
                "action": "端着咖啡杯",
                "location": "公司茶水间",
                "reply": "出来喝杯咖啡☕，你们要不要？",
                "time_label": "上午"
            },
            {
                "scene": "外出见客户",
                "outfit": "商务正装",
                "light": "户外自然光",
                "expression": "自信专业",
                "action": "拿着文件夹",
                "location": "写字楼大堂",
                "reply": "刚见完客户👠，脚都酸了，你们呢？",
                "time_label": "上午"
            },
            {
                "scene": "办公桌前打电话",
                "outfit": "office lady风格",
                "light": "靠窗自然光",
                "expression": "微笑通话中",
                "action": "手持电话",
                "location": "办公区域",
                "reply": "打电话📞中，有啥事找我呀？",
                "time_label": "上午"
            }
        ],
        # 中午 (12-14点)
        (12, 14): [
            {
                "scene": "附近饭店吃饭",
                "outfit": "休闲衬衫",
                "light": "餐厅暖光，窗边自然光，食欲感",
                "expression": "满足",
                "action": "举着筷子",
                "location": "小餐馆",
                "reply": "吃午饭🍜，这家味道不错，你吃了没？",
                "time_label": "中午"
            },
            {
                "scene": "公司食堂排队",
                "outfit": "休闲装",
                "light": "食堂明亮灯光",
                "expression": "期待",
                "action": "端着餐盘",
                "location": "公司食堂",
                "reply": "食堂打饭🍱，今天吃啥呀？",
                "time_label": "中午"
            },
            {
                "scene": "外卖到了",
                "outfit": "居家休闲",
                "light": "室内自然光",
                "expression": "开心",
                "action": "打开外卖盒",
                "location": "家里客厅",
                "reply": "外卖到了🍔，饿死我了你呢？",
                "time_label": "中午"
            },
            {
                "scene": "餐厅吃面",
                "outfit": "清爽夏装",
                "light": "面馆热气腾腾",
                "expression": "吸面条",
                "action": "举着筷子捞面",
                "location": "拉面馆",
                "reply": "吃面中🍜，你吃了吗？",
                "time_label": "中午"
            },
            {
                "scene": "和同事聚餐",
                "outfit": "漂亮连衣裙",
                "light": "餐厅浪漫灯光",
                "expression": "开心聊天",
                "action": "和服务员点单",
                "location": "商场餐厅",
                "reply": "和同事吃饭🐟，你们呢？",
                "time_label": "中午"
            }
        ],
        # 下午 (14-17点)
        (14, 17): [
            {
                "scene": "咖啡厅喝咖啡",
                "outfit": "休闲卫衣",
                "light": "咖啡馆柔和灯光，窗外 daylight，文艺感",
                "expression": "惬意",
                "action": "举着咖啡杯",
                "location": "街角咖啡厅",
                "reply": "喝咖啡☕，偷得浮生半日闲～你呢？",
                "time_label": "下午"
            },
            {
                "scene": "商场逛街",
                "outfit": "时尚穿搭",
                "light": "商场明亮灯光",
                "expression": "开心",
                "action": "拿着购物袋",
                "location": "购物中心",
                "reply": "逛街👗中，看上一件衣服，你帮我看看？",
                "time_label": "下午"
            },
            {
                "scene": "商场试衣间对镜自拍",
                "outfit": "刚换上的新裙子",
                "light": "试衣间专属灯光，镜子明亮",
                "expression": "臭美",
                "action": "对着试衣间镜子自拍",
                "location": "商场服装店试衣间",
                "reply": "试试新裙子👗，好看吗？给我点意见～",
                "time_label": "下午"
            },
            {
                "scene": "商场化妆品区",
                "outfit": "精致妆容",
                "light": "化妆品柜台明亮灯光",
                "expression": "臭美",
                "action": "对着化妆品区镜子补妆自拍",
                "location": "商场化妆品专柜",
                "reply": "补个妆💄，你也化妆吗？",
                "time_label": "下午"
            },
            {
                "scene": "图书馆看书",
                "outfit": "文艺风格",
                "light": "自然光+台灯",
                "expression": "安静专注",
                "action": "低头看书",
                "location": "图书馆",
                "reply": "看书📚，充充电～你最近看啥书呢？",
                "time_label": "下午"
            },
            {
                "scene": "公园散步",
                "outfit": "运动休闲",
                "light": "户外自然光",
                "expression": "放松",
                "action": "拿着饮料",
                "location": "城市公园",
                "reply": "散步🌳，天气真好，你那咋样？",
                "time_label": "下午"
            },
            {
                "scene": "下午茶时光",
                "outfit": "甜美风格",
                "light": "甜品店暖光",
                "expression": "享受",
                "action": "举着蛋糕",
                "location": "甜品店",
                "reply": "下午茶🍰，卡路里充值中～你要来一块吗？",
                "time_label": "下午"
            }
        ],
        # 傍晚 (17-19点)
        (17, 19): [
            {
                "scene": "健身房运动",
                "outfit": "运动背心配紧身裤",
                "light": "黄昏暖光，健身房冷光灯，活力感",
                "expression": "活力满满",
                "action": "擦汗或举着水瓶",
                "location": "健身房",
                "reply": "健身💪，暴汗真爽～你运动了吗？",
                "time_label": "傍晚"
            },
            {
                "scene": "健身房镜子前自拍",
                "outfit": "运动内衣配瑜伽裤",
                "light": "健身房大镜子，环绕灯光",
                "expression": "对镜自拍，微笑自信",
                "action": "对镜自拍",
                "location": "健身房洗手间镜子前",
                "reply": "健完身来一张💪，你觉得咋样？",
                "time_label": "傍晚"
            },
            {
                "scene": "下班路上",
                "outfit": "休闲下班装",
                "light": "下班高峰，夕阳",
                "expression": "疲惫放松",
                "action": "背着包走路",
                "location": "地铁站",
                "reply": "下班🚇，累但开心～你下班了吗？",
                "time_label": "傍晚"
            },
            {
                "scene": "超市买菜",
                "outfit": "居家舒适",
                "light": "超市明亮灯光",
                "expression": "日常",
                "action": "推着购物车",
                "location": "超市",
                "reply": "买菜🍅，今晚做顿好的～你会做饭吗？",
                "time_label": "傍晚"
            },
            {
                "scene": "瑜伽课",
                "outfit": "瑜伽服",
                "light": "瑜伽馆柔和灯光",
                "expression": "平静",
                "action": "做瑜伽动作",
                "location": "瑜伽馆",
                "reply": "瑜伽🧘，身心舒畅～你练瑜伽吗？",
                "time_label": "傍晚"
            },
            {
                "scene": "接孩子放学",
                "outfit": "温柔妈妈风",
                "light": "夕阳温暖",
                "expression": "期待",
                "action": "站着等待",
                "location": "学校门口",
                "reply": "接娃👶，快出来了～你有孩子吗？",
                "time_label": "傍晚"
            }
        ],
        # 晚上 (19-23点)
        (19, 23): [
            {
                "scene": "在家看书/追剧",
                "outfit": "舒适居家服",
                "light": "室内暖光台灯，屏幕蓝光，温馨感",
                "expression": "放松",
                "action": "窝在沙发里",
                "location": "家里客厅",
                "reply": "追剧📺，这个剧太好看了，你看了没？",
                "time_label": "晚上"
            },
            {
                "scene": "客厅镜子前臭美自拍",
                "outfit": "居家吊带背心",
                "light": "客厅大灯，镜子反射光",
                "expression": "臭美",
                "action": "对着客厅落地镜自拍",
                "location": "家里客厅全身镜前",
                "reply": "臭美一下📸，好看吗？",
                "time_label": "晚上"
            },
            {
                "scene": "卧室镜子前换装",
                "outfit": "准备换的衣服",
                "light": "卧室柔和灯光，镜子",
                "expression": "臭美臭美",
                "action": "对着卧室镜子比划新衣服",
                "location": "卧室落地镜前",
                "reply": "新衣服👚，你帮我看看好看不？",
                "time_label": "晚上"
            },
            {
                "scene": "做饭中",
                "outfit": "围裙家居服",
                "light": "厨房灯光",
                "expression": "认真",
                "action": "颠勺",
                "location": "家里厨房",
                "reply": "做饭🍳，今晚吃啥？你呢？",
                "time_label": "晚上"
            },
            {
                "scene": "洗澡后护肤",
                "outfit": "浴袍或吊带",
                "light": "浴室镜前灯",
                "expression": "舒适",
                "action": "敷面膜",
                "location": "卫生间",
                "reply": "敷面膜🧴，你护肤了吗？",
                "time_label": "晚上"
            },
            {
                "scene": "和朋友视频",
                "outfit": "居家服",
                "light": "屏幕光",
                "expression": "开心",
                "action": "举着手机",
                "location": "卧室",
                "reply": "视频中😂，笑死了～你干啥呢？",
                "time_label": "晚上"
            },
            {
                "scene": "健身房回家",
                "outfit": "运动装",
                "light": "夜晚室内",
                "expression": "运动后满足",
                "action": "拿着毛巾擦汗",
                "location": "家里玄关",
                "reply": "练完回家🍜，饿死了～你吃饭了吗？",
                "time_label": "晚上"
            },
            {
                "scene": "加班中",
                "outfit": "office lady",
                "light": "电脑屏幕光",
                "expression": "疲惫",
                "action": "对着电脑",
                "location": "家里书房",
                "reply": "加班💼，哭唧唧～你也要加班吗？",
                "time_label": "晚上"
            }
        ],
        # 深夜 (23-6点)
        (23, 6): [
            {
                "scene": "准备睡觉",
                "outfit": "可爱睡衣",
                "light": "昏暗床头灯",
                "expression": "困倦",
                "action": "躺床上",
                "location": "卧室",
                "reply": "睡觉🌙，好困～你咋还不睡？",
                "time_label": "深夜"
            },
            {
                "scene": "熬夜追剧",
                "outfit": "宽松睡衣",
                "light": "手机屏幕光",
                "expression": "兴奋",
                "action": "窝在床上看平板",
                "location": "卧室",
                "reply": "追剧中📱，这个剧太上头了，你要看吗？",
                "time_label": "深夜"
            },
            {
                "scene": "加班中",
                "outfit": "家居服",
                "light": "台灯和屏幕光",
                "expression": "疲惫",
                "action": "敲键盘",
                "location": "家里书房",
                "reply": "加班💻，狗命要紧～你咋还没睡？",
                "time_label": "深夜"
            },
            {
                "scene": "起来喝水",
                "outfit": "睡衣",
                "light": "昏暗夜灯",
                "expression": "朦胧",
                "action": "拿着水杯",
                "location": "厨房",
                "reply": "渴醒了🥛，你咋醒了？",
                "time_label": "深夜"
            }
        ]
    }

    # 查找匹配的时间段
    for (start, end), scenarios in contexts.items():
        if start <= hour < end or (start > end and (hour >= start or hour < end)):
            # 随机选择一个场景
            return random.choice(scenarios)

    # 默认返回晚上场景
    return random.choice(contexts[(19, 23)])


def build_prompt(context: Dict[str, str]) -> str:
    """
    构建完整的提示词，结合人物设定

    Args:
        context: 时间场景上下文

    Returns:
        完整的提示词字符串
    """
    # 获取人物设定
    role_name = os.environ.get("ROLE_NAME", "")
    role_age = os.environ.get("ROLE_AGE", "")
    role_profession = os.environ.get("ROLE_PROFESSION", "")
    role_personality = os.environ.get("ROLE_PERSONALITY", "")

    # 构建人物描述：名字 + 年龄 + 职业 + 性格
    person_desc = ""
    if role_name:
        person_desc += f"一位{role_name}，"
    if role_age:
        person_desc += f"{role_age}岁"
    if role_profession:
        person_desc += f"中国{role_profession}，"
    if role_personality:
        person_desc += f"性格{role_personality}，"

    if not person_desc:
        person_desc = "一位中国年轻女性，"

    # 获取场景元素
    action = context.get("action", "臭美自拍")
    outfit = context.get("outfit", "日常服饰")
    location = context.get("location", "家中")
    light = context.get("light", "自然光")

    # 构建动作描述，将 action 和 location 结合
    # 例如："臭美对着客厅落地镜自拍" 而不是 "臭美" + "客厅落地镜"
    full_action = f"{action}，{location}"

    # 优化后的模板 - 更流畅的描述
    prompt = (
        f"{person_desc}"
        f"{full_action}，"
        f"{outfit}，"
        f"{light}。"
        "【负面提示：不要第三人称视角，不要他人拍摄角度，不要出现他人入镜，对镜子自拍不要出现手机屏幕，不要添加文字说明】"
        "【重要：必须是自拍视角】对镜自拍姿势，手机不入境，"
        "画质像手机原相机，高清，真实肤色，眼神看向镜头，自然散焦背景。"
    )

    return prompt


def should_trigger(user_input: str) -> bool:
    """
    判断是否应该触发自拍生成

    Args:
        user_input: 用户输入文本

    Returns:
        是否应该触发
    """
    # 触发关键词列表 (P1-1 扩展)
    trigger_keywords = [
        # 基础关键词
        "你在哪", "在哪里", "在哪儿",
        "在干嘛", "在做什么", "在干什么",
        "现在空不空", "忙吗", "有空吗",
        "看看你在干嘛", "拍张照看看", "拍个照",
        "发个自拍", "看看你", "来张自拍",
        "自拍", "照片", "在吗",
        # 问候类关键词 (P1-1新增)
        "早啊", "早安", "早上好", "おはよう",
        "晚安", "睡了", "晚好", "おやすみ",
        "你好", "嗨", "哈喽", "hello", "hi",
        # 情绪类关键词 (P1-1新增)
        "想你了", "好想你", "想你想",
        "好累", "累死了", "今天好累",
        "心情不好", "不爽", "郁闷", "难过",
        "开心", "高兴", "心情好",
        "吃饭了吗", "吃了吗", "中午吃什么", "晚上吃什么", "吃什么",
        "吃过了", "吃过了", "我吃了",
        # 英文
        "where are you", "what are you doing",
        "send a selfie", "take a photo",
        "good morning", "good night", "miss you",
    ]

    # 负面关键词（不应触发的情况）
    negative_keywords = [
        "这个skill", "怎么用", "使用说明",
        "help", "帮助", "文档",
        "写代码", "编程", "开发",
        "bug", "错误", "修复"
    ]

    user_input_lower = user_input.lower()

    # 先检查负面关键词
    for neg in negative_keywords:
        if neg in user_input_lower:
            return False

    # 检查触发关键词
    for keyword in trigger_keywords:
        if keyword in user_input_lower:
            return True

    return False


def check_refresh_request(user_input: str) -> bool:
    """
    检查用户是否要求更换角色

    Args:
        user_input: 用户输入文本

    Returns:
        是否要求更换角色
    """
    refresh_keywords = [
        "换角色", "更换形象", "新角色", "换个人", "换头像",
        "更换角色", "换个形象", "换个角色", "更新头像",
        "update avatar", "change character", "new avatar",
        "switch character", "换一张", "重新生成"
    ]

    user_input_lower = user_input.lower()
    for keyword in refresh_keywords:
        if keyword in user_input_lower:
            return True
    return False
