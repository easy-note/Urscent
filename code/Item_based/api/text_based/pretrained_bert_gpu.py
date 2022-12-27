import os

import torch
from pytorch_pretrained_bert import BertTokenizer, BertModel, BertForMaskedLM

import pandas as pd
import numpy as np

from tqdm import tqdm
import pickle

def word_embedding(text):
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

    marked_text = "[CLS] " + text + " [SEP]"

    tokenized_text = tokenizer.tokenize(marked_text)

    # Map the token strings to their vocabulary indeces.
    indexed_tokens = tokenizer.convert_tokens_to_ids(tokenized_text)
        
    segments_ids = [1] * len(tokenized_text)

    # Python list를 PyTorch tensor로 변환하기 
    tokens_tensor = torch.tensor([indexed_tokens]).to(device)
    segments_tensors = torch.tensor([segments_ids]).to(device)

    # 미리 학습된 모델(가중치) 불러오기
    model = BertModel.from_pretrained('bert-base-uncased').to(device)

    # 모델 "evaluation" 모드 : feed-forward operation
    model.eval()

    # 각 레이어의 은닉상태 확인하기
    # Run the text through BERT, and collect all of the hidden states produced
    # from all 12 layers. 
    with torch.no_grad():
        encoded_layers, _ = model(tokens_tensor, segments_tensors)
        
    token_embeddings = torch.stack(encoded_layers, dim=0)
    # print(token_embeddings.size()) # torch.Size([12, 1, 22, 768])

    token_embeddings = torch.squeeze(token_embeddings, dim=1)
    # print(token_embeddings.size())  # torch.Size([12, 22, 768])

    token_embeddings = token_embeddings.permute(1,0,2)
    # print(token_embeddings.size())  # torch.Size([22, 12, 768])

    '''
    token_vecs_cat = []
    for token in token_embeddings :
        cat_vec = torch.cat((token[-1], token[-2], token[-3], token[-4]), dim=0)
        
        token_vecs_cat.append(cat_vec)
        
    print ('Shape is: %d x %d' % (len(token_vecs_cat), len(token_vecs_cat[0])))
    # Shape is: 22 x 3072 (768*4)


    token_vecs_sum = []
    for token in token_embeddings:
        
        sum_vec = torch.sum(token[-4:], dim=0)
        token_vecs_sum.append(sum_vec)
    '''
    
    token_vecs = encoded_layers[11][0][0]
    
    # print(type(encoded_layers[11][0][0]))
    # print(encoded_layers[11][0][0].shape)
    
    return token_vecs


def main():
    

    data = pd.read_csv('/private/sogang_fragrance/assets/csv/item_table_sim.csv')
    data = data.fillna('0'*100)
    text_data = data['text'].tolist()
    
    X = np.empty((0, 768), dtype=np.float32) 
    
    # min len = 68
    for text in tqdm(text_data, desc='Calculating...') :
        x = word_embedding(text) # (765,)
        x = x.unsqueeze(dim=0)
        
        # print(x.cpu().detach().numpy().shape)
        
        X = np.append(X, x.cpu().detach().numpy(), axis=0)
        
        
    np.save('bert_embedding_{}-gpu.npy'.format(np.shape(X)), X)
        

        
        
    
    
    
if __name__ == '__main__':
    device = torch.device("cuda:0")
    
    main()