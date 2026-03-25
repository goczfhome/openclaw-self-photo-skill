#!/usr/bin/env python3
import os
import sys

# 设置 API Key（运行时会被环境变量覆盖，这里设置默认值）
# 用户可以通过环境变量 SELF_PHOTO_API_KEY 覆盖
if 'SELF_PHOTO_API_KEY' not in os.environ:
    # 从缓存文件读取
    CACHE_FILE = os.path.join(os.path.dirname(__file__), ".api_key_cache.json")
    if os.path.exists(CACHE_FILE):
        try:
            import json
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                api_key = cache.get("api_key")
                if api_key:
                    os.environ['SELF_PHOTO_API_KEY'] = api_key
        except:
            pass

sys.path.insert(0, os.path.dirname(__file__))
import generate_selfie
generate_selfie.main()
