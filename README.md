# 拍友 - OpenClaw 虚拟角色自拍技能

让 AI 虚拟角色在对话中主动分享自拍照。

## 功能

- 根据时间段自动选择场景（早安/工作/用餐/晚安等）
- 生成符合角色设定的图片 + 走心配文
- 自动上传到飞书，发送图片而非链接
- 支持用户自建服务部署

## 目录结构

```
openclaw-self-photo-skill/
├── SKILL.md                    # 技能定义文档
├── scripts/
│   ├── api_client.py          # API 客户端
│   └── generate_selfie.py     # 主控脚本
└── README.md
```

## 快速开始

### 1. 获取 API Key
访问拍友平台注册账号，获取 Key。

### 2. 配置到飞书
在飞书对话中发送：
```
设置自拍APIKey sp_xxxxxxxxxxxxxxxx
```

### 3. 开始使用
```
发个自拍
看看你今天在干嘛
早啊
晚安
```

## 技术支持
邮箱：goczfhome@gmail.com

## 许可证
MIT
