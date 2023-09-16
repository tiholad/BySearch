import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from datasets import load_dataset, load_from_disk


class BySearch:
    def get_embeddings(self, text_list):
        encoded_input = self.tokenizer(
            text_list, padding=True, truncation=True, return_tensors="pt", max_length=64,
        )
        encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
        model_output = self.model(**encoded_input)
        return model_output.last_hidden_state[:, 0]
    
    
    def __init__(self, device, dataset=None, path=None, checkpoint="KoichiYasuoka/roberta-small-belarusian", compute_embeddings=False):
        self.device     = device
        self.checkpoint = checkpoint
        self.tokenizer  = AutoTokenizer.from_pretrained(checkpoint)
        self.model      = AutoModel.from_pretrained(checkpoint)
        self.model.to(device)
        
        self.path = path
        if dataset is not None:
            self.database = dataset
        elif path is not None:
            self.database = load_from_disk(path)
        
        if compute_embeddings:
            self.database = self.database.map(
                lambda x: {"embedding": self.get_embeddings(x["text"]).detach().cpu().numpy()}, 
                batched=True, 
            )
        self.database.add_faiss_index('embedding')
        
    
    def search(self, prompt):
        embedding = self.get_embeddings([prompt]).detach().cpu().numpy()
        scores, samples = self.database.get_nearest_examples('embedding', embedding, k=5)
        results_df = pd.DataFrame.from_dict(samples)
        results_df['scores'] = scores
        results_df.sort_values('scores', ascending=False, inplace=True)
        for _, row in results_df.iterrows():
            print(f'Scores: {row.scores}')
            print(f'URL: {row.url}')
            print(f'Text: {row.text}')
            print(148 * '-')