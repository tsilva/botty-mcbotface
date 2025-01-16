import random
import gradio as gr

def chatbot(message, history):
    return random.choice(["Yes", "No"])


demo = gr.ChatInterface(
    fn=chatbot,
    title="Botty McBotface",
    description="Your friendly neighborhood chatbot",
    examples=["Hello!", "What's the weather like?", "Tell me a joke"],
    #retry_btn=True,
    #undo_btn=True,
    #clear_btn=True,
)

demo.launch()
