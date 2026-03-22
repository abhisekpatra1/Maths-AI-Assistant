import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List

model_name = "gemini-2.5-flash"   # replace with Llama/Qwen/Mistral in production
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
model.eval()



# Markov Process Token Sampler

def markov_next_token(prev_token_id, context_embedding, temperature=1.0):
    """
    Computes P(x_t | x_{t-1}) and samples next token stochastically.
    """
    input_ids = torch.tensor([[prev_token_id]])
    with torch.no_grad():
        logits = model(input_ids).logits[:, -1, :]  # P(next | previous)
        logits = logits / temperature               # Temperature from your slide
        probs = torch.softmax(logits, dim=-1)

        # Weighted by RAG context (posterior influence)
        if context_embedding is not None:
            probs = probs * context_embedding       # Bayesian conditioning
            probs = probs / probs.sum()

        next_token = torch.multinomial(probs, num_samples=1).item()
        return next_token



# RAG-Enhanced Markov Text Generator

def markov_rag_generate(query: str,
                        retrieved_docs: List[str],
                        steps=60,
                        temperature=0.5):

    # 1) Convert retrieved docs → embedding-based influence vector
    context_text = " ".join(retrieved_docs)
    tokens = tokenizer(context_text, return_tensors="pt").input_ids[0]

    # Convert context to influence weights (simple version → average attention mass)
    with torch.no_grad():
        emb = model(tokens).logits.mean(dim=0)
        context_embedding = torch.softmax(emb, dim=-1)

    # 2) Start sequence with query prompt
    input_ids = tokenizer.encode(query, return_tensors="pt")[0]
    prev_token_id = input_ids[-1]

    generated = [prev_token_id]

    # 3) Markov sampling loop → P(x_t | x_{t-1})
    for _ in range(steps):
        next_id = markov_next_token(prev_token_id, context_embedding, temperature)
        generated.append(next_id)
        prev_token_id = next_id

    text = tokenizer.decode(generated, skip_special_tokens=True)
    return text.strip()
