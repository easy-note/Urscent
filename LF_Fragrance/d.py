import pickle
import pdb
with open("/home/dhkim/Fragrance/data/rating_data.pkl","rb") as fr:
    data = pickle.load(fr)
    for i in data:
        print(i)