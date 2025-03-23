import gradio as gr
import json
from typing import Dict, Any
from web_server import process_question

TRANSLATIONS = {
    "zh": {
        "title": "DevOps查询助手",
        "description": "👋 你好！我是你的DevOps助手。请输入你关于各个Domain Server相关问题，我会帮你查询并解释结果。",
        "language": "语言选择",
        "clear_btn": "清空对话",
        "retry_btn": "重试",
        "loading": "正在查询中...",
        "error": "抱歉，处理您的请求时出现错误: {}",
        "examples": [
            "我们一共有多少个domain",
            "在dev1 domain中，一共有多少个server正在运行configportal service",
            "请列出staging domain中所有运行logserver service 的服务器IP和它们的servergroup"
        ],
        "sql_section": "执行的SQL语句：",
        "result_section": "查询结果：",
        "summary_section": "结果说明："
    },
    "en": {
        "title": "DevOps Assistant",
        "description": "👋 Hi! I'm your DevOps assistant. Please enter your question about domain and server, and I'll help you query and explain the results.",
        "language": "Language",
        "clear_btn": "Clear Chat",
        "retry_btn": "Retry",
        "loading": "Querying...",
        "error": "Sorry, an error occurred: {}",
        "examples": [
            "How many domains do we have?",
            "In dev1, how many servers are running the configportal service?",
            "Please list all the server IPs and their servergroups running the logserver service in the staging domain."
        ],
        "sql_section": "Executed SQL:",
        "result_section": "Query Results:",
        "summary_section": "Summary:"
    }
}

class SQLChatBot:
    def __init__(self):
        self.current_lang = "zh"
    
    def switch_language(self, lang: str) -> Dict[str, str]:
        """Switch interface language and return new interface text"""
        self.current_lang = "zh" if lang == "中文" else "en"
        return TRANSLATIONS[self.current_lang]
    
    def format_response(self, response: Dict[str, Any]) -> str:
        """Format the response message with proper sections and formatting"""
        trans = TRANSLATIONS[self.current_lang]
        
        formatted_msg = f"**{trans['sql_section']}**\n```sql\n{response['sql']}\n```\n\n"
        formatted_msg += f"**{trans['result_section']}**\n```json\n{json.dumps(response['result'], indent=2, ensure_ascii=False)}\n```\n\n"
        formatted_msg += f"**{trans['summary_section']}**\n{response['summary']}"
        
        return formatted_msg

    def process_query(self, message: str, history: list) -> tuple:
        """Process user query and return formatted response"""
        try:
            response = process_question(message)
            formatted_response = self.format_response(response)
            history.append((message, formatted_response))
            return history, "", history
        except Exception as e:
            error_msg = TRANSLATIONS[self.current_lang]["error"].format(str(e))
            history.append((message, error_msg))
            return history, "", history

def create_interface():
    """Create and configure the Gradio interface"""
    bot = SQLChatBot()
    
    with gr.Blocks(css="#chatbot {height: 600px} .message { font-size: 15px }") as demo:
        # Language selection
        with gr.Row():
            language_radio = gr.Radio(
                choices=["中文", "English"],
                value="中文",
                label="语言/Language",
                interactive=True
            )
        
        # Title and description
        title = gr.Markdown(f"# {TRANSLATIONS['zh']['title']}")
        description = gr.Markdown(TRANSLATIONS['zh']['description'])
        
        # Chat interface
        chatbot = gr.Chatbot(height=400)
        msg = gr.Textbox(
            placeholder=TRANSLATIONS['zh']['description'],
            show_label=False
        )
        
        # Control buttons
        with gr.Row():
            clear = gr.Button(TRANSLATIONS['zh']['clear_btn'])
            submit = gr.Button("Send", variant="primary")
        
        # Example questions
        gr.Examples(
            examples=TRANSLATIONS['zh']['examples'],
            inputs=msg
        )

        # Setup chat functionality
        state = gr.State([])

        submit_click = submit.click(
            bot.process_query,
            inputs=[msg, state],
            outputs=[chatbot, msg, state],
            show_progress=True
        )

        msg.submit(
            bot.process_query,
            inputs=[msg, state],
            outputs=[chatbot, msg, state],
            show_progress=True
        )

        clear.click(lambda: ([], "", []), outputs=[chatbot, msg, state])
        
        # Language change handler
        def on_language_change(lang):
            """Handle language change events"""
            trans = bot.switch_language(lang)
            return (
                f"# {trans['title']}",
                trans['description'],
                trans['clear_btn'],
                trans['description']  # Update textbox placeholder
            )
        
        # Register language change event
        language_radio.change(
            fn=on_language_change,
            inputs=[language_radio],
            outputs=[
                title,
                description,
                clear,
                msg  # Update textbox placeholder
            ]
        )
    
    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        favicon_path="🤖"
    ) 