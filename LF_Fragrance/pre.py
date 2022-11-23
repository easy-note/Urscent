import config
import pandas as pd
import numpy as np
import seaborn as sns
from ast import literal_eval
import math
from collections import Counter
import pdb
import os
import re
from tqdm import tqdm
from sklearn.preprocessing import MultiLabelBinarizer
import argparse
from itertools import repeat
from collections import defaultdict
import pycountry_convert as pc
import numpy as np
import pandas as pd
import warnings
import pickle
import multiprocessing as mp
from joblib import Parallel, delayed
import sys
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler, StandardScaler,LabelEncoder


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
    def __init__(self, df, columns_list, name, sig):
        self.columns = columns_list
        self.sig = sig
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
        for i in tqdm(self.df.index):
            input = self.df.loc[i,:]
            row = np.zeros(len(input))
            count = self.count[i]
            if count == 0: result.append(row)

            else:
                for i in range(len(input)):
                    row[i] = input[i]
                zero = [i for i, e in enumerate(row) if e == 0]

                if self.sig == True: 
                    row = row * self.custom_sigmoid(count)
                    left = 100 - np.nansum(row)
                    if left != 0:
                        left = left / len(zero)
                        for i in zero:
                            row[i] = left
                        result.append(row)
                    else: result.append(row)
                elif self.sig == False: result.append(row)

        result =  pd.DataFrame(result, columns = self.columns[:])
        result.index = self.df.index
        return result

def get_common(item_table,rating_table):
    #pdb.set_trace()
    fragrance_name=np.array(list(item_table['name']))
    rating_table.rename(columns={'name':'fragrance'}, inplace = True)
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

def parallel_notes(item_table, notes_info):
    item_table['top_notes'] = item_table['top_notes'].fillna('[]')
    item_table['base_notes'] = item_table['base_notes'].fillna('[]')
    item_table['heart_notes'] = item_table['heart_notes'].fillna('[]')
    item_table['top_literal'] = item_table['top_notes'].apply(lambda x: get_parent(notes_info, x))
    item_table['base_literal'] = item_table['base_notes'].apply(lambda x: get_parent(notes_info, x))
    item_table['heart_literal'] = item_table['heart_notes'].apply(lambda x: get_parent(notes_info, x))
    item_table['notes_literal'] =  item_table['top_literal'] + " "+ item_table['base_literal'] + " "+ item_table['heart_literal']
    notes_df = item_table['notes_literal'].str.get_dummies(" ")
    print('--------------------done--------------------')
    return notes_df


def train_preprocessing(item_table, rating_table, notes_info, all_filed, cat_field, cont_field, user = False):
    field_dict = defaultdict(list)
    field_index = []

    rating_table.drop('brand', axis = 1, inplace = True)
    
    
    print('--------------------user categorical field--------------------')
    #user_gender_df
    print('--------------------'+ 'processing user gender'+ '--------------------')
    rating_table = rating_table.rename(columns={'gender':'user_gender'})
    user_gender_df = rating_table['user_gender'].str.get_dummies()
    rating_table.drop('user_gender', axis = 1, inplace = True)
    rating_table = pd.concat([rating_table, user_gender_df], axis = 1)
    field_dict['user_gender'] = list(user_gender_df.columns)

    #nation_df
    print('--------------------'+ 'processing nation'+ '--------------------')
    nation_df = rating_table['continent'].str.get_dummies()
    rating_table.drop(['continent','nation'], axis = 1, inplace = True)
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
    
    #item_table.drop(['Type_count','Season_count','Audience_count','Occasion_count'], axis = 1, inplace = True)

    input = get_common(item_table,rating_table)

    field_dict['rating'] = ['rating']
    field_dict['Scent'] = ['Scent']
    field_dict['Sillage'] = ['Sillage']
    field_dict['Longevity'] = ['Longevity']
    field_dict['Value for money'] = ['Value for money']

    seasons = ['Spring','Summer','Fall','Winter']
    occasions = ['Leisure','Daily','Night Out','Business','Sport','Evening']
    audiences = ['Old','Young','Men','Women']
    types_list = config.types_list

    for columns in [seasons, audiences, occasions, types_list]:
        for column in columns:
            field_dict[column] = [column]

    print('--------------------item categorical field--------------------')
    #Gender_df
    print('--------------------'+ 'processing gender'+'--------------------')
    gender_df = input.gender.str.get_dummies()
    input.drop('gender', axis = 1, inplace = True)
    input = pd.concat([input, gender_df], axis = 1)
    field_dict['gender'] = list(gender_df.columns)

    #year_df
    print('--------------------'+'processing year'+ '--------------------')
    input.year = input.year.astype("int32")
    bins = list(range(1900, 2030, 10))
    bins.append(1370)
    bins = sorted(bins)
    labels = list(range(len(bins) - 1))
    labels = ["year_" + str(i) for i in labels]
    input.year = pd.cut(input['year'], bins=bins, right=True, labels=labels)
    year_df = pd.get_dummies(input.year)
    input = pd.concat([input, year_df], axis=1)
    input.drop("year", axis=1, inplace=True)
    field_dict['year'] = list(year_df.columns)

    #brands_df
    print('--------------------'+ 'processing brands'+ '--------------------')
    br_encoder = LabelEncoder()
    input['brand'] = br_encoder.fit_transform(input.brand.values)
    input['brand'] = input['brand'].astype(str)
    brands_df = input.brand.str.get_dummies()
    input.drop('brand', axis = 1, inplace = True)
    input = pd.concat([input, brands_df], axis = 1)
    field_dict['brand'] = list(brands_df.columns)

    #perfumer_df
    print('--------------------'+ 'processing perfumer'+ '--------------------')
    input['perfumer'] = input['perfumer'].fillna('[]')
    input['perfumer_literal'] = input['perfumer'].apply(to_liter)
    perfumer_df = input['perfumer_literal'].str.get_dummies(" ")
    input = pd.concat([input, perfumer_df], axis=1)
    input.drop(['perfumer','perfumer_literal'], axis=1, inplace=True)
    field_dict['perfumer'] = list(perfumer_df.columns)

    #notes 
    print('--------------------'+ 'processing notes'+ '--------------------')

    input['top_notes'] = input['top_notes'].fillna('[]')
    input['base_notes'] = input['base_notes'].fillna('[]')
    input['heart_notes'] = input['heart_notes'].fillna('[]')
    input['top_literal'] = input['top_notes'].apply(lambda x: get_parent(notes_info, x))
    input['base_literal'] = input['base_notes'].apply(lambda x: get_parent(notes_info, x))
    input['heart_literal'] = input['heart_notes'].apply(lambda x: get_parent(notes_info, x))
    input['notes_literal'] =  input['top_literal'] + " "+ input['base_literal'] + " "+ input['heart_literal']
    notes_df = input['notes_literal'].str.get_dummies(" ")

    input = pd.concat([input, notes_df], axis=1)
    input.drop(['top_notes','base_notes','heart_notes','top_literal','base_literal','heart_literal','notes_literal'], axis=1, inplace=True)
    field_dict['notes'] = list(notes_df.columns)


    #user_id_df
    if user == True:
        user_df = input['user_id'].str.get_dummies().add_prefix('u_')
        input = pd.concat([input, user_df], axis = 1)
        field_dict['user_id'] = list(user_df.columns)
    else: all_filed.remove('user_id')

    input.drop('user_id', axis = 1, inplace = True)
    Y = pd.Series([1 if (int(x)>= 8) else 0 for x in input['user_rating']])
    input.drop(['user_rating','fragrance'], axis = 1, inplace = True)

    field_index = []
    for i,column in enumerate(all_filed):
        if column in set(cat_field):
            #if i == 42: pdb.set_trace()
            field_index.extend(list(repeat(i, len(field_dict[column]))))
        else: field_index.append(i)

    X = input

    return X, Y, field_dict, field_index

def Bayesian_rating(item_table):
    rating = Bayesian_adj(item_table, 'rating','rating_count')
    item_table['rating'] = rating.bayesian_rating(item_table.rating_count, item_table.rating)
    item_table.drop("rating_count", axis=1, inplace=True)
    item_table['rating'] = item_table['rating'].fillna(item_table['rating'].mean(skipna = True))

    scent = Bayesian_adj(item_table, 'Scent','Scent_count')
    item_table['Scent'] = scent.bayesian_rating(item_table.Scent_count, item_table.Scent)
    item_table.drop("Scent_count", axis=1, inplace=True)
    item_table['Scent'] = item_table['Scent'].fillna(item_table['Scent'].mean(skipna = True))

    longevity = Bayesian_adj(item_table, 'Longevity','Longevity_count')
    item_table['Longevity'] = longevity.bayesian_rating(item_table.Longevity_count, item_table.Longevity)
    item_table.drop("Longevity_count", axis=1, inplace=True)
    item_table['Longevity'] = item_table['Longevity'].fillna(item_table['Longevity'].mean(skipna = True))

    sillage = Bayesian_adj(item_table, 'Sillage','Sillage_count')
    item_table['Sillage'] = sillage.bayesian_rating(item_table.Sillage_count, item_table.Sillage)
    item_table.drop("Sillage_count", axis=1, inplace=True)
    item_table['Sillage'] = item_table['Sillage'].fillna(item_table['Sillage'].mean(skipna = True))

    price_value = Bayesian_adj(item_table, 'Value for money','Value for money_count')
    item_table['Value for money'] = price_value.bayesian_rating(item_table['Value for money_count'], item_table['Value for money'])
    item_table.drop("Value for money_count", axis=1, inplace=True)
    item_table['Value for money'] = item_table['Value for money'].fillna(item_table['Value for money'].mean(skipna = True))
    
    return item_table

def parallelize_preprocessing(item_table, rating_table, notes_info, mode):
    #nation_df

    print('--------------------'+ 'processing nation'+ '--------------------')
    rating_table['continent'] = rating_table['nation'].apply(lambda x : get_continent(x))
    

    print('--------------------'+ 'processing type'+ '--------------------')
    
    types = item_table.loc[:,'Type']
    types_list = list(set(convert_data(types)))
    types_dict = key_value(types_list)

    types_df = pd.DataFrame(columns = types_list)
    item_table['Type'] = item_table['Type'].fillna('{}')
    for i in tqdm(item_table.index):
        types_dict = literal_eval(item_table.loc[i, 'Type'])
        types_df = types_df.append(types_dict, ignore_index = True)
    
    types_df.index = item_table.index
    item_table = pd.concat([item_table, types_df], axis=1)
    item_table.drop("Type", axis=1, inplace=True)


    seasons = ['Spring','Summer','Fall','Winter']
    occasions = ['Leisure','Daily','Night Out','Business','Sport','Evening']
    audiences = ['Old','Young','Men','Women']

    if (mode == 'sim') or (mode == 'train'):
        type_enc = Encoder(item_table, types_list, 'Type', False)
        season_enc = Encoder(item_table, seasons, 'Season', False)
        occasion_enc = Encoder(item_table, occasions , 'Occasion', False)
        audience_enc = Encoder(item_table, audiences, 'Audience',False)
    else: 
        type_enc = Encoder(item_table, types_list, 'Type', True)
        season_enc = Encoder(item_table, seasons, 'Season', True)
        occasion_enc = Encoder(item_table, occasions , 'Occasion', True)
        audience_enc = Encoder(item_table, audiences, 'Audience', True)

    #Type
    item_table[types_list] = type_df = type_enc.encoder()
    #Season
    print('--------------------'+ 'processing season'+ '--------------------')
    item_table[seasons] = season_enc.encoder()
    #Occasion
    print('--------------------'+ 'processing occasion'+ '--------------------')
    item_table[occasions] = occasion_enc.encoder()
    #Audience
    print('--------------------'+'processing audience'+ '--------------------')
    item_table[audiences] = audience_enc.encoder()
    item_table.drop(['Type_count','Audience_count','Season_count','Occasion_count'], axis = 1,inplace = True)

    if mode != 'sim': item_table.drop(['text','img_url'], axis = 1,inplace = True)
    elif mode == 'sim' :item_table.drop('img_url', axis = 1,inplace = True)

    if mode == 'db':
        #perfumer_df
        print('--------------------'+ 'processing perfumer'+ '--------------------')
        item_table['perfumer'] = item_table['perfumer'].fillna('[]')
        item_table['perfumer'] = item_table['perfumer'].apply(lambda x: str(x).replace('[','').replace(']','').replace(',','|'))
        #notes 
        item_table['top_notes'] = item_table['top_notes'].fillna('[]')
        item_table['base_notes'] = item_table['base_notes'].fillna('[]')
        item_table['heart_notes'] = item_table['heart_notes'].fillna('[]')
        print('--------------------'+ 'processing top notes'+ '--------------------')
        item_table['top_literal'] = item_table['top_notes'].apply(lambda x: get_parent(notes_info, x))
        print('--------------------'+ 'processing base notes'+ '--------------------')
        item_table['base_literal'] = item_table['base_notes'].apply(lambda x: get_parent(notes_info, x))
        print('--------------------'+ 'processing heart notes'+ '--------------------')
        item_table['heart_literal'] = item_table['heart_notes'].apply(lambda x: get_parent(notes_info, x))

        t_notes_df = item_table['top_literal'].str.get_dummies(" ")
        b_notes_df = item_table['base_literal'].str.get_dummies(" ")
        h_notes_df = item_table['heart_literal'].str.get_dummies(" ")

        top_notes = pd.concat([item_table.iloc[:,:3], t_notes_df], axis=1)
        base_notes = pd.concat([item_table.iloc[:,:3], b_notes_df], axis=1)
        heart_notes = pd.concat([item_table.iloc[:,:3], h_notes_df], axis=1)

        item_table.drop(['top_notes','base_notes','heart_notes','top_literal','base_literal','heart_literal'], axis = 1, inplace = True)
        print('--------------------'+ 'done'+ '--------------------')
        return [item_table, rating_table , top_notes, base_notes, heart_notes]

    elif mode == 'train':
        return [item_table, rating_table]

    elif mode == 'sim':
        item_table['perfumer'] = item_table['perfumer'].apply(lambda x: str(x).replace('[','').replace(']','').replace(',','|'))
        item_table['top_notes'] = item_table['top_notes'].fillna('[]')
        item_table['base_notes'] = item_table['base_notes'].fillna('[]')
        item_table['heart_notes'] = item_table['heart_notes'].fillna('[]')
        print('--------------------'+ 'processing top notes'+ '--------------------')
        item_table['top_notes'] = item_table['top_notes'].apply(lambda x: get_parent(notes_info, x))
        print('--------------------'+ 'processing base notes'+ '--------------------')
        item_table['base_notes'] = item_table['base_notes'].apply(lambda x: get_parent(notes_info, x))
        print('--------------------'+ 'processing heart notes'+ '--------------------')
        item_table['heart_notes'] = item_table['heart_notes'].apply(lambda x: get_parent(notes_info, x))
        return [item_table, rating_table]

    

    

if __name__ == '__main__':

    mode = sys.argv[-1]
    print(mode)
    num_core = os.cpu_count()
    warnings.simplefilter(action='ignore', category=FutureWarning)

    if mode == 'DB':
        item_table = pd.read_csv(config.item_table_path, encoding ='utf-8-sig')
        rating_table = pd.read_csv(config.rating_table_path, encoding ='utf-8-sig')
        notes_info =  pd.read_csv(config.notes_info_path,index_col=[0,1])

        item_table_chunks = np.array_split(item_table, num_core)
        rating_table_chunks = np.array_split(rating_table, num_core)

        print('Parallelizing with ' +str(num_core)+'cores')
        with Parallel(n_jobs = num_core, backend="multiprocessing") as parallel:
            results = parallel(delayed(parallelize_preprocessing)(item_table_chunks[i],rating_table_chunks[i], notes_info,'db') for i in range(num_core))

        for i,data in enumerate(results):
            if i == 0:
                item_table = data[0]
                rating_table = data[1]
                top_notes = data[2]
                base_notes = data[3]
                heart_notes = data[4]
            else:
                item_table = pd.concat([item_table, data[0]], axis = 0)
                rating_table = pd.concat([rating_table, data[1]], axis = 0)
                top_notes = pd.concat([top_notes, data[2]], axis = 0)
                base_notes = pd.concat([base_notes, data[3]], axis = 0)
                heart_notes = pd.concat([heart_notes , data[4]], axis = 0)


        item_table.to_csv('/home/dhkim/Fragrance/data/item_table.csv' ,encoding ='utf-8-sig',  index=False)
        rating_table.to_csv('/home/dhkim/Fragrance/data/rating_table.csv' ,encoding ='utf-8-sig',  index=False)
        top_notes.to_csv('/home/dhkim/Fragrance/data/top_notes.csv' ,encoding ='utf-8-sig',  index=False)
        base_notes.to_csv('/home/dhkim/Fragrance/data/base_notes.csv' ,encoding ='utf-8-sig',  index=False)
        heart_notes.to_csv('/home/dhkim/Fragrance/data/heart_notes.csv' ,encoding ='utf-8-sig',  index=False)

    elif mode == 'train':
        item_table = pd.read_csv(config.item_table_path, encoding ='utf-8-sig')
        item_table = Bayesian_rating(item_table)

        rating_table = pd.read_csv(config.rating_table_path, encoding ='utf-8-sig')
        notes_info =  pd.read_csv(config.notes_info_path,index_col=[0,1])
        
        #type_avg_count = item_table['Type_count'].mean(skipna = True)
        #season_avg_count = item_table['Season_count'].mean(skipna = True)
        #occasion_avg_count = item_table['Occasion_count'].mean(skipna = True)
        #audience_avg_count = item_table['Audience_count'].mean(skipna = True)

        item_table_chunks = np.array_split(item_table, num_core)
        rating_table_chunks = np.array_split(rating_table, num_core)

        print('Parallelizing with ' +str(num_core)+'cores')
        with Parallel(n_jobs = num_core, backend="multiprocessing") as parallel:
            results = parallel(delayed(parallelize_preprocessing)(item_table_chunks[i],rating_table_chunks[i], notes_info, 'train') for i in range(num_core))

        for i,data in enumerate(results):
            
            if i == 0:
                item_table = data[0]
                rating_table = data[1]
            else:
                item_table = pd.concat([item_table, data[0]], axis = 0)
                rating_table = pd.concat([rating_table, data[1]], axis = 0)
        all_filed = config.ALL_FIELDS
        cat_field = config.CAT_FIELDS
        cont_fields = config.CONT_FIELDS

        X, Y, field_dict, field_index = train_preprocessing(item_table, rating_table, notes_info, all_filed, cat_field, cont_fields)
        X.to_csv('/home/dhkim/Fragrance/data/X_2.csv' ,encoding ='utf-8-sig',  index=False)
        Y.to_csv('/home/dhkim/Fragrance/data/Y_2.csv' ,encoding ='utf-8-sig',  index=False)
        with open('/home/dhkim/Fragrance/data/field_dict_2.pkl','wb') as f:
                pickle.dump(field_dict,f)
        with open('/home/dhkim/Fragrance/data/field_index_2.pkl','wb') as f:
                pickle.dump(field_index ,f)

    elif mode == 'sim':
        item_table = pd.read_csv(config.item_table_path, encoding ='utf-8-sig')
        rating_table = pd.read_csv(config.rating_table_path, encoding ='utf-8-sig')
        notes_info =  pd.read_csv(config.notes_info_path,index_col=[0,1])
    
        item_table_chunks = np.array_split(item_table, num_core)
        rating_table_chunks = np.array_split(rating_table, num_core)

        print('Parallelizing with ' +str(num_core)+'cores')
        with Parallel(n_jobs = num_core, backend="multiprocessing") as parallel:
            results = parallel(delayed(parallelize_preprocessing)(item_table_chunks[i],rating_table_chunks[i], notes_info,'sim') for i in range(num_core))

        for i,data in enumerate(results):
            if i == 0:
                item_table = data[0]
                rating_table = data[1]
            else:
                item_table = pd.concat([item_table, data[0]], axis = 0)
                rating_table = pd.concat([rating_table, data[1]], axis = 0)


        item_table.to_csv('/home/dhkim/Fragrance/data/item_table_sim.csv' ,encoding ='utf-8-sig',  index=False)
        rating_table.to_csv('/home/dhkim/Fragrance/data/rating_table_sim.csv' ,encoding ='utf-8-sig',  index=False)

