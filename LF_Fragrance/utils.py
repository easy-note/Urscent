import pandas as pd
import numpy as np
import seaborn as sns
from ast import literal_eval
import math
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler, StandardScaler
import pandas as pd
import os
import numpy as np
import re
from tqdm import tqdm
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.preprocessing import StandardScaler
import argparse
from sklearn.preprocessing import StandardScaler
from itertools import repeat
from collections import defaultdict
import pycountry_convert as pc
from sklearn.preprocessing import MinMaxScaler

class Bayesian_adj:
  def __init__(self, df, column, count_column):
    self.df = df
    self.column = self.df[column]
    self.count = self.df[count_column]
    self.N = self.count.sum(skipna=True)
    self.NR = (self.column * self.count).sum()

  def bayesian_rating(self, n, r):
    return (self.NR  + n * r) / (self.N + n)

def convert_data(datas):
    result = []
    for i in datas:
        try:
            result.extend(literal_eval(i))
        except Exception:
            continue
    return result

def get_unique_values_list_data(column):
    data_list = [x for x in column.values]
    return list(set(sum(data_list, [])))

def get_unique_values_string_data(column):
    data_list = [x for x in column.values]
    return list(set(data_list))

def key_value(unique_value_list):
    result = {}
    for i in range(len(unique_value_list)):
        result[unique_value_list[i]] = i
    return result   

class Encoder:
    def __init__(self, df, columns_list, name):
        self.columns = columns_list
        self.df = df[self.columns]
        
        self.count = df[name+'_count']
        self.avg_count = df[name+'_count'].mean(skipna = True)
        self.count =  df[name+'_count'].fillna(0)
        for column in columns_list:
            self.df[column] = self.df[column].fillna(0)
        print(self.df.columns)
                    
    def custom_sigmoid(self, x):
        return 1 / (1 +np.exp(-x/self.avg_count))
  
    def encoder(self):
      result = []

      for i in tqdm(range(len(self.df))):
        input = self.df.loc[i,:]

        row = np.zeros(len(input))
        count = self.count[i]
        
        for i in range(len(input)):
             row[i] = input[i]
        if count == 0: result.append(row)
        else:
          row = row * self.custom_sigmoid(count)
          zero = [i for i, e in enumerate(row) if e == 0]

          left = 100 - np.nansum(row)

          if left != 0:
              left = left / len(zero)
              for i in zero:
                  row[i] = left
              result.append(row)
          else: result.append(row)

      result =  pd.DataFrame(result, columns = self.columns[:] )
      #scaler = StandardScaler()
      scaler = MinMaxScaler()
      return scaler.fit_transform(result)

def get_common(item_table,rating_table):

    fragrance_name=np.array(list(item_table['name']))

    encoder = LabelEncoder()
    encoder.fit(fragrance_name)

    common_index = []

    for fragrance in list(set(list(item_table['name']))&set(list(rating_table['fragrance']))):
        common_index.append(rating_table.index[(rating_table['fragrance'] == fragrance)].tolist()[0])

    item_table['name'] = encoder.transform(item_table['name'])
    rating_table = rating_table.loc[common_index,:]
    rating_table['fragrance'] = encoder.transform(rating_table['fragrance'])
    
    encoder.fit(rating_table['user_id'])
    rating_table['user_id'] = encoder.transform(rating_table['user_id'])
    
    result = pd.merge(rating_table, item_table, left_on = 'fragrance', right_on = 'name', how = 'inner').sort_values(by=['user_id'])
    result.drop('name', axis = 1 ,inplace = True)
    result['fragrance'] = rating_table['fragrance'].astype(str)
    result['user_id'] = rating_table['user_id'].astype(str)
    return result

def get_continent(country):
  try:
    country_code = pc.country_name_to_country_alpha2(country, cn_name_format="default")
    return  pc.country_alpha2_to_continent_code(country_code)
  except:
    return 'ETC'


def find_parent_notes(notes_info, note):
    return notes_info[notes_info['child note']== note].index.values

def get_parent(notes_info, note_list):
    note_list = literal_eval(note_list)
    if len(note_list) != None:
        result = []
        for note in note_list:
            parents = find_parent_notes(notes_info, note)
            for parent in parents:
                parent = parent[0].replace(" ", "")
                result.append(parent)
    return (' ').join(result)
def to_liter(list_data):
    list_data = literal_eval(list_data)
    for i in range(len(list_data)):
        list_data[i] = list_data[i].replace(" ", '')
    return (' ').join(list_data)




