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
            'Tobacco', 'Woodynotes',
            'Aldehydes', 'Amber', 'Animalicnotes', 'Aquaticnotes', 'Balsamicnotes', 
            'Citricnotes', 'Earthynotes', 'Floralnotes', 'Fragranceingredients', 
            'Fruitynotes', 'Gourmandynotes', 'Grain', 'Greennotes', 'Herbaceousnotes', 
            'Mineralnotes', 'Mossynotes', 'Musk', 'Notclassified', 'Orientalnotes', 
            'Powderynotes', 'Resinousnotes', 'Smokynotes', 'Spicynotes', 'Textilenotes', 
            'Tobacco', 'Woodynotes',
            'Aldehydes', 'Amber', 'Animalicnotes', 'Aquaticnotes', 'Balsamicnotes', 
            'Citricnotes', 'Earthynotes', 'Floralnotes', 'Fragranceingredients', 
            'Fruitynotes', 'Gourmandynotes', 'Grain', 'Greennotes', 'Herbaceousnotes', 
            'Mineralnotes', 'Mossynotes', 'Musk', 'Notclassified', 'Orientalnotes', 
            'Powderynotes', 'Resinousnotes', 'Smokynotes', 'Spicynotes', 'Textilenotes', 
            'Tobacco', 'Woodynotes'] # len(notes) = 26 * 3

def cos_sim(A, B):
  return dot(A, B)/(norm(A)*norm(B))

def top_onehot_embedding(li):
    base_np = np.zeros(26*3)
    
    try:
        for i in li.split(' '):
            base_np[notes_ids.index(i)] = 1
    except:
        try:
            base_np[notes_ids.index(i)] = 1
        except:
            pass
        
    return base_np

def heart_onehot_embedding(li, prev):
    try:
        for i in li.split(' '):
            prev[notes_ids.index(i)+26] = 1
    except:
        try:
            prev[notes_ids.index(i)+26] = 1
        except:
            pass
        
    return prev
        
        
def base_onehot_embedding(li, prev):
    try:
        for i in li.split(' '):
            prev[notes_ids.index(i)+(26*2)] = 1
    except:
        try:
            prev[notes_ids.index(i)+(26*2)] = 1
        except:
            pass
        
    return prev
        
    

data = pd.read_csv('/private/sogang_fragrance/assets/csv/item_table_sim.csv')

top_notes = data['top_notes'].tolist()
heart_notes = data['heart_notes'].tolist()
base_notes = data['base_notes'].tolist()

fragrance_list = data['name'].tolist()

X = np.empty((0, 26*3), dtype=np.float32) 
print(X.shape)
for (t, h, b) in tqdm(zip(top_notes, heart_notes, base_notes), desc='Cal Onehot...'):
    onehot = top_onehot_embedding(t)
    onehot = heart_onehot_embedding(h, onehot)
    onehot = base_onehot_embedding(b, onehot)
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

score_df.to_csv('./note_based-all.csv')