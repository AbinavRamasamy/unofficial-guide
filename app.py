"""
Milestone 5 — Gradio Query Interface
Run with: python app.py
"""

import gradio as gr
from src.generate import generate


def ask(question: str) -> tuple[str, str]:
    if not question.strip():
        return "Please enter a question.", ""
    return generate(question)

with gr.Blocks(title="Rutgers Unofficial Guide") as demo:
    gr.Markdown("# Rutgers Unofficial Guide\nAsk anything about courses and professors at Rutgers NB.")

    with gr.Row():
        question = gr.Textbox(label="Your question", placeholder="Which professor should I take for CS111?", scale=4)
        submit = gr.Button("Ask", variant="primary", scale=1)

    answer  = gr.Textbox(label="Answer",  lines=8,  interactive=False)
    sources = gr.Textbox(label="Sources", lines=4,  interactive=False)

    submit.click(fn=ask, inputs=question, outputs=[answer, sources])
    question.submit(fn=ask, inputs=question, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
