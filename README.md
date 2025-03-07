# 智能英语学习助手 🤖

![Python版本](https://img.shields.io/badge/Python-3.8%2B-blue)
![许可证](https://img.shields.io/badge/License-MIT-green)
![OpenAI集成](https://img.shields.io/badge/LLM-GPT4-turquoise)

> 自动化监控学习进度 + 智能生成测试题 + 邮件报告系统

## 项目概述 🎯

本工具自动扫描指定目录中的英语学习文件，通过大语言模型（GPT-4）分析学习内容，生成包含测试题、复习指南的PDF报告，并支持邮件自动推送。适用于：

- 英语自学者 📚
- 教育机构 🏫
- 在线课程平台 💻

## 核心功能 ✨

### 📂 智能目录监控
- 实时检测`./study_records`目录变化
- 自动处理新增`.txt`/`.md`文件
- 归档已处理文件至`~/processed`

### 🧠 智能内容生成
- 生成30道混合题型测试题（填空/选择/翻译）
- 创建语法重点复习卡片
- 提供详细答案解析
- 每日学习进度总结

### 📧 自动化报告系统
- 支持SMTP邮件推送（Gmail）
- 自发送模式支持
- 加密传输（TLS）

### ⚙️ 高度可配置
```yAML
# 示例配置
llm:
  model: "gpt-4-turbo"  # 支持所有OpenAI模型
```

## 快速开始 🚀

### 依赖安装
```bash
conda create -n learning-assistant python=3.12
conda activate learning-assistant
# Python库
pip install watchdog python-dotenv pdfkit pyyaml
```

### 配置文件
1. 复制`config.yaml`为`myconfig.yaml`
```bash
SMTP_USER="your-email@example.com"
SMTP_PASSWORD="app-password"
MY_EMAIL="recipient@example.com"
OPENAI_API_KEY="sk-your-openai-key"
```

2. 编辑`config.yaml`
```yaml
monitor:
  study_dir: "~/english_study"  # 监控目录路径

smtp:
  server: "smtp.gmail.com"     # 邮件服务商配置
```

## 运行系统 ▶️
```bash
python assistant.py --config myconfig.yaml
```

## 使用示例 📖
1. 在监控目录添加学习文件
```text
# vocabulary.txt
persistent - 持续的
comprehensive - 全面的
```

2. 自动生成报告样例
```text
📘 英语学习报告 2024-03-20

1. 选择题
[ ] The ______ study helped me improve quickly.
A) persistent  B) temporary  C) random 

✅ 答案：A) persistent
📝 解析：persistent表示"持续的"，符合长期学习语境...
```

3. 接收邮件报告
```
发件人：study-assistant@your-domain.com
主题：📌 您的英语学习报告已生成（含3个新知识点）
```

## 故障排查 🔧

| 现象                 | 解决方法                     |
|----------------------|----------------------------|
| SMTP认证失败         | 检查应用密码/开启SMTP服务    |
| 文件未处理           | 检查文件扩展名是否为.txt/.md |
| API调用超限         | 切换备用LLM模型             |

## 项目结构 📂
```
.
├── config.yaml            # 主配置文件
├── assistant.py           # 启动脚本
└── english_study_helper.log      # 运行日志
└── study_records          # 学习记录目录
    ├── 20250224.md        # 学习记录文件
    └── 20250225.md
└── processed             # 已处理文件
```

## 授权许可 📜
本项目基于 [MIT License](LICENSE) 开放使用

---

**让英语学习更高效！** 🚀 如有问题，请提交Issue或联系camerondomenic786@gmail.com