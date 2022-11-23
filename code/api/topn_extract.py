import os
import glob

import pandas as pd
import numpy as np

import csv
from tqdm import tqdm

def main(assets_path, k):
    row_data = pd.read_csv(assets_path, index_col = 0)
    cols = row_data.columns
    
    recommend_list = []
    
    for idx, i in enumerate(tqdm(range(len(row_data)), desc='Calculating ...')):
    
        score = np.array(row_data.iloc[i].tolist())
        score[np.isnan(score)] = -100 # nan 제거
        
        x = np.argsort(score)[::-1][:k]
        max_indices = list(cols[x])
        max_indices.insert(0, cols[idx])
        recommend_list.append(max_indices)
        
    save_path = '/private/sogang_fragrance/code/results/note_based2/recommend'
    os.makedirs(save_path, exist_ok=True)
    
    col = ['target']
    for i in range(k):
        col.append(str(i+1)+'rank')
        
    with open(os.path.join(save_path, 'top-{}.csv'.format(k)), 'w', newline='') as f: 
        write = csv.writer(f) 
        
        write.writerow(col) 
        write.writerows(recommend_list)
        
    
    

if __name__ == '__main__':
    # main(assets_path='/private/sogang_fragrance/code/results/note_based/note_based_cos_sim.csv', k=1)
    # main(assets_path='/private/sogang_fragrance/code/results/note_based/note_based_cos_sim.csv', k=3)
    # main(assets_path='/private/sogang_fragrance/code/results/note_based/note_based_cos_sim.csv', k=5)
    # main(assets_path='/private/sogang_fragrance/code/results/note_based/note_based_cos_sim.csv', k=7)
    # main(assets_path='/private/sogang_fragrance/code/results/note_based/note_based_cos_sim.csv', k=9)
    # main(assets_path='/private/sogang_fragrance/code/results/note_based/note_based_cos_sim.csv', k=10)
    
    main(assets_path='/private/sogang_fragrance/code/results/note_based_cos_sim2.csv', k=1)
    main(assets_path='/private/sogang_fragrance/code/results/note_based_cos_sim2.csv', k=3)
    main(assets_path='/private/sogang_fragrance/code/results/note_based_cos_sim2.csv', k=5)
    main(assets_path='/private/sogang_fragrance/code/results/note_based_cos_sim2.csv', k=7)
    main(assets_path='/private/sogang_fragrance/code/results/note_based_cos_sim2.csv', k=9)
    main(assets_path='/private/sogang_fragrance/code/results/note_based_cos_sim2.csv', k=10)
    
    