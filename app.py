"""Gradio interface for The Unofficial Guide."""
import gradio as gr
from query import ask
from embed import build_store

print("Loading embedding model and building vector store...")
client, collection, model = build_store()
print("Ready!\n")

def handle_query(question):
    if not question.strip():
        return "Please enter a question.", ""
    result = ask(question, collection, model)
    sources = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources

with gr.Blocks(title="The Unofficial Guide - CSI CS Professors") as demo:
    gr.Markdown("# The Unofficial Guide\n### CSI Computer Science Professor Reviews")
    inp = gr.Textbox(label="Ask a question about CSI CS professors", placeholder="e.g. Does Professor Zhang help students during labs?")
    btn = gr.Button("Ask")
    answer = gr.Textbox(label="Answer", lines=10)
    sources = gr.Textbox(label="Sources used", lines=4)
    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

demo.launch()