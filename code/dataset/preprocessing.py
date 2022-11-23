

import os
import re
import math
import pandas as pd
import numpy as np
import argparse

from tqdm import tqdm
import seaborn as sns
from ast import literal_eval
from collections import Counter

import torch
import torch.nn as nn
import tensorflow as tf
from tensorflow import keras

import gensim.models
import pdb

from itertools import repeat
from collections import defaultdict
import pycountry_convert as pc

import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler, StandardScaler, LabelEncoder, MultiLabelBinarizer

import pickle
import warnings

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
      #return scaler.fit_transform(result)
      return result

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


def preprocessing(item_table, rating_table, notes_info, all_filed, cat_field, cont_fields):
  field_dict = defaultdict(list)
  field_index = []

  #Gender_df
  print('--------------------'+ 'processing gender'+'--------------------')
  gender_df = item_table.gender.str.get_dummies()
  item_table.drop('gender', axis = 1, inplace = True)
  item_table = pd.concat([item_table, gender_df], axis = 1)
  field_dict['gender'] = list(gender_df.columns)

  #year_df
  print('--------------------'+'processing year'+ '--------------------')
  item_table.year = item_table.year.astype("int32")
  bins = list(range(1900, 2030, 10))
  bins.append(1370)
  bins = sorted(bins)
  labels = list(range(len(bins) - 1))
  labels = ["year_" + str(i) for i in labels]
  item_table.year = pd.cut(item_table['year'], bins=bins, right=True, labels=labels)
  year_df = pd.get_dummies(item_table.year)
  item_table = pd.concat([item_table, year_df], axis=1)
  item_table.drop("year", axis=1, inplace=True)
  field_dict['year'] = list(year_df.columns)


  print('--------------------'+ 'processing rating'+'--------------------')
  rating_info =['rating','Scent','Longevity','Sillage','Value for money']
  rating = Bayesian_adj(item_table, 'rating','rating_count')
  item_table['rating'] = rating.bayesian_rating(item_table.rating_count, item_table.rating)
  item_table.drop("rating_count", axis=1, inplace=True)
  item_table['rating'] = item_table['rating'].fillna(item_table['rating'].mean(skipna = True))
  field_dict['rating'] = ['rating']

  scent = Bayesian_adj(item_table, 'Scent','Scent_count')
  item_table['Scent'] = scent.bayesian_rating(item_table.Scent_count, item_table.Scent)
  item_table.drop("Scent_count", axis=1, inplace=True)
  item_table['Scent'] = item_table['Scent'].fillna(item_table['Scent'].mean(skipna = True))
  field_dict['Scent'] = ['Scent']

  longevity = Bayesian_adj(item_table, 'Longevity','Longevity_count')
  item_table['Longevity'] = longevity.bayesian_rating(item_table.Longevity_count, item_table.Longevity)
  item_table.drop("Longevity_count", axis=1, inplace=True)
  item_table['Longevity'] = item_table['Longevity'].fillna(item_table['Longevity'].mean(skipna = True))
  field_dict['Longevity'] = ['Longevity']

  sillage = Bayesian_adj(item_table, 'Sillage','Sillage_count')
  item_table['Sillage'] = sillage.bayesian_rating(item_table.Sillage_count, item_table.Sillage)
  item_table.drop("Sillage_count", axis=1, inplace=True)
  item_table['Sillage'] = item_table['Sillage'].fillna(item_table['Sillage'].mean(skipna = True))
  field_dict['Sillage'] = ['Sillage']

  price_value = Bayesian_adj(item_table, 'Value for money','Value for money_count')
  item_table['Value for money'] = price_value.bayesian_rating(item_table['Value for money_count'], item_table['Value for money'])
  item_table.drop("Value for money_count", axis=1, inplace=True)
  item_table['Value for money'] = item_table['Value for money'].fillna(item_table['Value for money'].mean(skipna = True))
  field_dict['Value for money'] = ['Value fmor money']


  scaler = StandardScaler()
  item_table[rating_info] =  scaler.fit_transform(item_table[rating_info])


  #notes 
  print('--------------------'+ 'processing notes'+ '--------------------')
  # item_table['perfumer'] = item_table['perfumer'].fillna('[]')
  # item_table['perfumer_literal'] = item_table['perfumer'].apply(to_liter)

  item_table['top_notes'] = item_table['top_notes'].fillna('[]')
  item_table['base_notes'] = item_table['base_notes'].fillna('[]')
  item_table['heart_notes'] = item_table['heart_notes'].fillna('[]')
  item_table['top_literal'] = item_table['top_notes'].apply(lambda x: get_parent(notes_info, x))
  item_table['base_literal'] = item_table['base_notes'].apply(lambda x: get_parent(notes_info, x))
  item_table['heart_literal'] = item_table['heart_notes'].apply(lambda x: get_parent(notes_info, x))
  item_table['notes_literal'] =  item_table['top_literal'] + " "+ item_table['base_literal'] + " "+ item_table['heart_literal']

  notes_df = item_table['notes_literal'].str.get_dummies(" ")

  item_table = pd.concat([item_table, notes_df], axis=1)
  item_table.drop(['top_notes','base_notes','heart_notes','top_literal','base_literal','heart_literal','notes_literal'], axis=1, inplace=True)
  field_dict['notes'] = list(notes_df.columns)

  print('--------------------'+ 'processing type'+ '--------------------')
  #Type
  types = item_table.loc[:,'Type']
  types_list = list(set(convert_data(types)))
  types_dict = key_value(types_list)

  types_df = pd.DataFrame(columns = types_list)
  item_table['Type'] = item_table['Type'].fillna('{}')
  for i in tqdm(range(len(item_table))):
    types_dict = literal_eval(item_table.loc[i, 'Type'])
    types_df = types_df.append(types_dict, ignore_index = True)

  item_table = pd.concat([item_table, types_df], axis=1)
  item_table.drop("Type", axis=1, inplace=True)
  
  type_enc = Encoder(item_table, types_list, 'Type')
  item_table[types_list] = type_df = type_enc.encoder()

  #Season
  print('--------------------'+ 'processing season'+ '--------------------')
  seasons = ['Spring','Summer','Fall','Winter']
  season_enc = Encoder(item_table, seasons, 'Season')
  item_table[seasons] = season_enc.encoder()
  #Occasion
  print('--------------------'+ 'processing occasion'+ '--------------------')
  occasions = ['Leisure','Daily','Night Out','Business','Sport','Evening']
  occasion_enc = Encoder(item_table, occasions , 'Occasion')
  item_table[occasions] = occasion_enc.encoder()
  #Audience
  print('--------------------'+'processing audience'+ '--------------------')
  audiences = ['Old','Young','Men','Women']
  audience_enc = Encoder(item_table, audiences, 'Audience')
  item_table[audiences] = audience_enc.encoder()

  item_table.drop(['Type_count','Season_count','Audience_count','Occasion_count'], axis=1, inplace=True)

  for columns in [types_list, seasons, occasions, audiences]:
    for column in columns:
      field_dict[column] = [column]

  item_table.drop(['brand','perfumer', 'text','img_url'], axis = 1,inplace = True)

  rating_table.drop('brand', axis = 1,inplace = True)
  #rating_table preprocessing



  print('--------------------'+ 'processing user'+ '--------------------')
  field_dict['user_rating'] = ['user_rating']
  #field_dict['user_id'] = ['user_id']
  #field_dict['fragrance'] = ['fragrance']

  #user_gender_df
  print('--------------------'+ 'processing user gender'+ '--------------------')
  rating_table = rating_table.rename(columns={'gender':'user_gender'})
  user_gender_df = rating_table['user_gender'].str.get_dummies()
  rating_table.drop('user_gender', axis = 1, inplace = True)
  rating_table = pd.concat([rating_table, user_gender_df], axis = 1)
  field_dict['user_gender'] = list(user_gender_df.columns)

  #nation_df
  print('--------------------'+ 'processing nation'+ '--------------------')
  rating_table['nation'] = rating_table['nation'].apply(lambda x : get_continent(x))
  nation_df = rating_table['nation'].str.get_dummies()
  rating_table.drop('nation', axis = 1, inplace = True)
  rating_table = pd.concat([rating_table, nation_df], axis = 1)
  field_dict['nation'] = list(nation_df.columns)

  #count_df
  print('--------------------'+ 'processing count'+ '--------------------')
  count = pd.DataFrame(rating_table['user_id'].value_counts())
  count = count.rename(columns={'user_id':'count'})
  count['user_id'] = count.index
  rating_table = pd.merge(rating_table, count, on = 'user_id', how = 'left').sort_values(by=['count'])
  rating_table['count'] = rating_table['count'].abs()
  rating_table['count'] = rating_table['count'].astype("int32")
  count_bin = pd.cut(rating_table['count'], 4, labels=False)
  count_bin = pd.Series(count_bin).astype('str')
  count_bin_col = pd.get_dummies(count_bin, prefix='count', prefix_sep='_')
  rating_table = pd.concat([rating_table, count_bin_col], axis=1)
  rating_table.drop('count', axis = 1, inplace = True)
  field_dict['count'] = list(count_bin_col.columns)

  input = get_common(item_table,rating_table)
  Y = pd.Series([1 if (int(x)>= 8) else 0 for x in input['user_rating']])
  input.drop('user_rating', axis = 1, inplace = True)

  #fragrance_df
  fragrance_df =  input['fragrance'].str.get_dummies()
  input.drop('fragrance', axis = 1, inplace = True)
  input = pd.concat([input, fragrance_df], axis = 1)
  field_dict['fragrance'] = list(fragrance_df.columns)

  #user_df
  user_df = input['user_id'].str.get_dummies()
  input.drop('user_id', axis = 1, inplace = True)
  input = pd.concat([input, user_df], axis = 1)
  field_dict['user_id'] = list(user_df.columns)

  field_index = []
  for i,column in enumerate(ALL_FIELDS):
    if column in set(CAT_FIELDS):
      field_index.extend(list(repeat(i, len(field_dict[column]))))
    else: field_index.append(i)
  
  X = input
  
  
  return X, Y, field_dict, field_index


if __name__ == '__main__':

    DB = pd.read_csv('./assets/csv/DB.csv', encoding ='utf-8-sig')
    rating_df = pd.read_csv('./assets/csv/rating_table.csv', encoding ='utf-8-sig')
    notes_info =  pd.read_csv('./assets/csv/notes_group.csv',index_col=[0,1])

    types = DB.loc[:,'Type']
    types_list = list(set(convert_data(types)))
    types_dict = key_value(types_list)
    ALL_FIELDS = ['user_gender', 'nation', 'count',
                'rating', 'Scent','Longevity', 'Sillage', 'Value for money', 
                'Spring', 'Summer', 'Fall',
                'Winter', 'Old', 'Young', 'Men', 'Women', 'Leisure', 'Daily',
                'Night Out', 'Business', 'Sport', 'Evening',
                'gender','year','notes',
                'Spicy', 'Creamy', 'Fougère', 'Citrus', 'Chypre', 'Aquatic', 'Gourmand', 'Fruity', 'Leathery', 'Earthy', 'Smoky', 'Resinous', 'Animal',
                'Powdery', 'Floral', 'Fresh', 'Woody', 'Green', 'Synthetic', 'Oriental','Sweet',
                'fragrance', 'user_id']

    CONT_FIELDS = ['user_rating', 'rating']
    CONT_FIELDS.extend(types_list)
    CONT_FIELDS.extend(['Spring','Summer','Fall','Winter'])
    CONT_FIELDS.extend(['Leisure','Daily','Night Out','Business','Sport','Evening'])
    CONT_FIELDS.extend(['Old','Young','Men','Women'])
    CONT_FIELDS.extend(['Scent','Longevity','Value for money','Sillage'])

    CAT_FIELDS = list(set(ALL_FIELDS).difference(CONT_FIELDS)) # ['year', 'fragrance', 'count', 'gender', 'user_gender', 'notes', 'nation', 'user_id']

    '''
    ##without id
    types = DB.loc[:,'Type']
    types_list = list(set(convert_data(types)))
    types_dict = key_value(types_list)
    ALL_FIELDS = ['user_rating', 'user_gender','nation','count', 
                'rating',
                'notes',
                'Scent', 'Longevity', 'Sillage', 'Value for money',
                'Spring', 'Summer', 'Fall', 'Winter', 
                'Old', 'Young', 'Men', 'Women',
                'Leisure', 'Daily', 'Night Out', 'Business', 'Sport', 'Evening',
                'Green','Fruity','Aquatic','Oriental','Earthy','Resinous','Gourmand','Smoky','Woody','Powdery','Fougère','Citrus','Chypre','Leathery','Creamy','Floral','Spicy','Sweet','Fresh','Animal','Synthetic',
                'gender', 'year']

    CONT_FIELDS = ['user_rating', 'rating']
    CONT_FIELDS.extend(types_list)
    CONT_FIELDS.extend(['Spring','Summer','Fall','Winter'])
    CONT_FIELDS.extend(['Leisure','Daily','Night Out','Business','Sport','Evening'])
    CONT_FIELDS.extend(['Old','Young','Men','Women'])
    CONT_FIELDS.extend(['Scent','Longevity','Value for money','Sillage'])

    CAT_FIELDS = list(set(ALL_FIELDS).difference(CONT_FIELDS))
    '''
    
    print('\n', '*'*100)
    print('DB')
    print(DB)
    print('\n')

    print('rating_df')
    print(rating_df)
    print('\n')

    print('notes_info')
    print(notes_info)
    print('\n')

    print('ALL_FIELDS')
    print(ALL_FIELDS)
    print('\n')

    print('CAT_FIELDS')
    print(CAT_FIELDS)
    print('\n')

    print('CONT_FIELDS')
    print(CONT_FIELDS)
    print('\n')
    print('*'*100, '\n')

    

    X, Y, field_dict, field_index = preprocessing(DB, rating_df, notes_info, ALL_FIELDS , CAT_FIELDS, CONT_FIELDS)

    with open('./train_X.pkl', 'wb') as f:
        pickle.dump(X, f, pickle.HIGHEST_PROTOCOL)

    with open('./test_Y.pkl', 'wb') as f:
        pickle.dump(Y, f, pickle.HIGHEST_PROTOCOL)

    with open('./field_dict.pkl', 'wb') as f:
        pickle.dump(field_dict, f, pickle.HIGHEST_PROTOCOL)

    with open('./field_index.pkl', 'wb') as f:
        pickle.dump(field_index, f, pickle.HIGHEST_PROTOCOL)
