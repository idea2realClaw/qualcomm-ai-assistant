---
name: qualcomm-ai-assistant
description: >
  高通文档网站 AI 助手交互 Skill。通过浏览器自动化访问 Qualcomm 文档网站的 AI Assistant，
  向其提问并获取基于高通官方文档的 AI 回复。
  
  触发场景：向高通AI提问、询问高通芯片信息、查询Qualcomm文档、问高通AI助手、
  高通文档AI、Qualcomm AI Assistant、IQ-9075相关问题、QCS系列芯片查询、
  高通开发板问题、Qualcomm芯片规格查询。
  
  适用产品：IQ-9075、QCS9075、QCS6490、QCS8250 等 Qualcomm IoT 产品线。
version: "1.0"
author: 龙竹
created: 2026-04-20
---

# Qualcomm AI Assistant Skill

通过浏览器自动化访问 Qualcomm 官方文档网站的 AI Assistant，发送问题并获取基于高通文档库的 AI 回复。

## 前置条件

- `playwright-cli` 已安装（`npm install -g @playwright/cli@latest`）
- 系统安装了 Edge 浏览器（Windows 环境默认可用）
- 网络可访问 `docs.qualcomm.com`

## 使用方法

```bash
# 基本用法 - 向 AI 助手提问
python scripts/ask_qualcomm_ai.py "What is IQ-9075?"

# 指定产品页面
python scripts/ask_qualcomm_ai.py "How to set up the development kit?" --product 1601111740076079

# 等待更长时间（复杂问题）
python scripts/ask_qualcomm_ai.py "Compare IQ-9075 with QCS8250" --timeout 60
```

## 工作流程

1. 使用 `playwright-cli` 打开 Edge 浏览器
2. 导航到指定的高通产品文档页面
3. 等待 AI Assistant 面板加载
4. 在输入框中填入问题
5. 按 Enter 发送
6. 等待 AI 生成回复（轮询检测 "Generating..." 状态消失）
7. 从页面快照中提取回复文本和引用来源
8. 关闭浏览器并返回结构化结果

## 输出格式

脚本输出为 JSON 格式，包含：
- `question`: 用户提出的问题
- `answer`: AI 助手的回复文本（Markdown 格式）
- `sources`: 引用的文档链接列表
- `product_url`: 当前产品页面 URL

## 注意事项

- AI 回复时间通常 15-30 秒，复杂问题可能需要更长时间
- 未登录时 AI 功能有限，建议登录高通开发者账号以获取更完整的文档访问
- 如果 "Generating..." 状态超过 60 秒未消失，视为超时
- 每次提问会开启新聊天（自动点击 "Start a new chat"）
