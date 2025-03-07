import argparse
import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

import markdown
import openai
import yaml
from tenacity import retry, stop_after_attempt, wait_exponential
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("english_study_helper.log"), logging.StreamHandler()],
)

parser = argparse.ArgumentParser(description="Assistant for daily English learning")
parser.add_argument(
    "--config", type=str, default="config.yaml", help="Path to the config file"
)
args = parser.parse_args()


# 配置信息
def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载并解析配置文件，支持：
    1. 环境变量替换（${VAR_NAME}格式）
    2. 路径展开（~扩展为家目录）
    3. 类型自动转换
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件未找到: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # 递归处理环境变量替换
    def replace_env_vars(data):
        if isinstance(data, dict):
            return {k: replace_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [replace_env_vars(v) for v in data]
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            var_name = data[2:-1]
            return os.getenv(var_name) or ""
        return data

    config = replace_env_vars(config)

    # 处理路径扩展
    if "monitor" in config:
        for dir_type in ["study_dir", "processed_dir"]:
            if dir_type in config["monitor"]:
                config["monitor"][dir_type] = os.path.expanduser(
                    config["monitor"][dir_type]
                )

    return config


CONFIG = load_config(args.config)


class FileHandler(FileSystemEventHandler):
    def __init__(self, assistant: "StudyAssistant"):
        super().__init__()
        self.assistant = assistant  # 持有StudyAssistant实例

    def on_created(self, event):
        """文件创建事件处理"""
        if not event.is_directory and event.src_path.endswith(".md"):
            logging.info(f"检测到新文件: {event.src_path}")
            try:
                # 调用StudyAssistant的处理方法
                self.assistant.process_file(event.src_path)
            except Exception as e:
                logging.error(f"文件处理失败: {str(e)}")


class StudyAssistant:
    def __init__(self):
        self.setup_dirs()
        self.file_handler = FileHandler(self)  # 注入当前实例

        self.init_process()

    def setup_dirs(self):
        """创建必要目录"""
        os.makedirs(CONFIG["monitor"]["study_dir"], exist_ok=True)
        os.makedirs(CONFIG["monitor"]["processed_dir"], exist_ok=True)

    def init_process(self):
        """初始化进程"""
        logging.info("初始化进程...")

        for file in os.listdir(CONFIG["monitor"]["study_dir"]):
            if file.endswith(".md"):
                file_path = os.path.join(CONFIG["monitor"]["study_dir"], file)
                try:
                    self.process_file(file_path)
                except Exception as e:
                    logging.error(f"初始化处理失败: {str(e)}")

    @retry(
        stop=stop_after_attempt(CONFIG["retry"]["max_attempts"]),
        wait=wait_exponential(
            multiplier=CONFIG["retry"]["delay_multiplier"],
            max=CONFIG["retry"]["max_delay"],
        ),
    )
    def generate_content(self, content: str) -> str:
        """调用LLM生成学习材料"""
        client = openai.OpenAI(
            api_key=CONFIG["llm"]["api_key"], base_url=CONFIG["llm"]["base_url"]
        )

        logging.info("Generating content from api")
        response = client.chat.completions.create(
            model=CONFIG["llm"]["model"],
            messages=[
                {
                    "role": "user",
                    "content": CONFIG["llm"]["prompt_template"].format(content=content),
                }
            ],
            temperature=1,
        )
        return response.choices[0].message.content

    def send_email(self, content: str):
        """发送优化样式的邮件"""
        msg = MIMEMultipart()
        msg["From"] = CONFIG["smtp"]["user"]
        msg["To"] = CONFIG["smtp"]["to"]
        msg["Subject"] = f"📚 英语学习日报 - {datetime.now().strftime('%Y-%m-%d')}"

        # 将Markdown转换为HTML
        html_content = markdown.markdown(content)

        # HTML版本
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 0.5em;">
                📖 今日学习报告
            </h2>
            <div style="
                background: #f8f9fa;
                padding: 1em;
                border-radius: 8px;
                border: 1px solid #ddd;
            ">{html_content}</div>
            <p style="color: #7f8c8d; font-size: 0.9em;">
                生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}
            </p>
        </div>
        """
        html_part = MIMEText(html_body, "html")

        msg.attach(html_part)

        # 发送邮件
        logging.info("Sending email...")
        with smtplib.SMTP(CONFIG["smtp"]["server"], CONFIG["smtp"]["port"]) as server:
            server.starttls()
            server.login(CONFIG["smtp"]["user"], CONFIG["smtp"]["password"])
            server.send_message(msg)

    def archive_file(self, src_path: str):
        """移动处理后的文件"""
        logging.info(f"Archiving file: {src_path}")
        if CONFIG["monitor"]["archive"]:
            filename = os.path.basename(src_path)
            dest_path = os.path.join(CONFIG["monitor"]["processed_dir"], filename)
            os.rename(src_path, dest_path)

    def process_file(self, file_path: str):
        """处理单个文件"""
        try:
            logging.info(f"Processing file: {file_path}")

            with open(file_path, "r") as f:
                content = f.read()

            # 生成学习材料
            study_material = self.generate_content(content)

            # 发送邮件
            self.send_email(study_material)

            # 归档文件
            self.archive_file(file_path)

            logging.info(f"Successfully processed: {file_path}")

        except Exception as e:
            logging.error(f"Failed to process {file_path}: {str(e)}")
            raise

    def run(self):
        """启动监控和定时任务"""
        observer = Observer()
        # 使用类内部的文件处理器
        observer.schedule(
            self.file_handler, CONFIG["monitor"]["study_dir"], recursive=True
        )
        observer.start()
        logging.info("开始监控文件系统...")

        # 持续运行
        try:
            while True:
                pass
        except KeyboardInterrupt:
            observer.stop()


if __name__ == "__main__":
    logging.info(CONFIG)

    assistant = StudyAssistant()
    assistant.run()
