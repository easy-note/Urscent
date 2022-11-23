'''
    - 각 향수 별로 26개의 노트를 onehot vector 로 임베딩
    - 향수 별 cos sim 유사도 측정
        - 다른 유사도 기법 (jaccard sim) 측정 가능할 듯?

    - 참고 사이트 (onehot vector cos sim)
        - https://wikidocs.net/24603
        - https://suy379.tistory.com/100
'''

import os

import numpy as np
from numpy import dot
from numpy.linalg import norm
np.set_printoptions(linewidth=np.inf)

import pandas as pd
from tqdm import tqdm

notes_ids  = ['Aldehydes', 'Amber', 'Animalicnotes', 'Aquaticnotes', 'Balsamicnotes', 
            'Citricnotes', 'Earthynotes', 'Floralnotes', 'Fragranceingredients', 
            'Fruitynotes', 'Gourmandynotes', 'Grain', 'Greennotes', 'Herbaceousnotes', 
            'Mineralnotes', 'Mossynotes', 'Musk', 'Notclassified', 'Orientalnotes', 
            'Powderynotes', 'Resinousnotes', 'Smokynotes', 'Spicynotes', 'Textilenotes', 
            'Tobacco', 'Woodynotes'] # len(notes) = 26

def cos_sim(A, B):
  return dot(A, B)/(norm(A)*norm(B))

def onehot_embedding(li):
    base_np = np.zeros(26)
    
    try:
        for i in li.split(' '):
            base_np[notes_ids.index(i)] = 1
    except:
        try:
            base_np[notes_ids.index(i)] = 1
        except:
            pass
        
    return base_np
        
    

data = pd.read_csv('/private/sogang_fragrance/assets/csv/item_table_sim.csv')
top_notes = data['top_notes'].tolist()
fragrance_list = data['name'].tolist()

X = np.empty((0, 26), dtype=np.float32) 
print(X.shape)
for i in tqdm(top_notes, desc='Cal Onehot...'):
    onehot = onehot_embedding(i)
    # print(onehot)
    X = np.append(X, np.expand_dims(onehot, axis=0), axis=0)

print(X.shape)

score_df = pd.DataFrame(columns = fragrance_list)


for i in tqdm(range(len(X)), desc='Calculating ...'):
    target_f = np.array(X[i,:])
    scores = []
    for j in range(len(X)):
        cos_f = np.array(X[j,:])

        scores.append(cos_sim(target_f, cos_f))
    
    score_df.loc[len(score_df)] = scores

score_df.to_csv('/private/sogang_fragrance/code/results/note_based_cos_sim_test.csv')