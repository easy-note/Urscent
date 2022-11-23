
import os
import numpy as np
from numpy import dot
from numpy.linalg import norm

import pandas as pd

from tqdm import tqdm


def cos_sim(A, B):
  return dot(A, B)/(norm(A)*norm(B))

np.set_printoptions(linewidth=np.inf)

text_embedding = np.load('/private/sogang_fragrance/code/api/text_based/bert_embedding_(59000, 768)-gpu.npy')

data = pd.read_csv('/private/sogang_fragrance/assets/csv/item_table_sim.csv')
fragrance_list = data['name'].tolist()
print('fragrance_list : ', fragrance_list)
score_df = pd.DataFrame(columns = fragrance_list)

for i in tqdm(range(len(text_embedding)), desc='Calculating ...'):
    target_f = np.array(text_embedding[i,:])
    scores = []
    for j in range(len(text_embedding)):
        cos_f = np.array(text_embedding[j,:])
        scores.append(cos_sim(target_f, cos_f))
    
    score_df.loc[len(score_df)] = scores

score_df.to_csv('/private/sogang_fragrance/code/results/text_based_cos_sim2.csv')
