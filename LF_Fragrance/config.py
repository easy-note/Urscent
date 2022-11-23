item_table_path = '/home/dhkim/Fragrance/data/DB.csv'
rating_table_path = '/home/dhkim/Fragrance/data/rating_table.csv'
notes_info_path = '/home/dhkim/Fragrance/data/notes_group.csv'

types_list = ['Citrus','Leathery','Aquatic','Earthy','Oriental','Animal','Green',
'Spicy','Fresh','Chypre','Floral','Powdery','Synthetic','Smoky',
'Woody','Gourmand','Creamy','Resinous','Fougère', 'Sweet','Fruity']

types_dict ={'Citrus': 0,'Leathery': 1, 'Aquatic': 2, 'Earthy': 3,
'Oriental': 4,'Animal': 5,'Green': 6,
'Spicy': 7,'Fresh': 8,'Chypre': 9,
'Floral': 10,'Powdery': 11,'Synthetic': 12,
'Smoky': 13,'Woody': 14,'Gourmand': 15,
'Creamy': 16,'Resinous': 17,'Fougère': 18, 
'Sweet': 19,'Fruity': 20}

ALL_FIELDS = ['user_gender', 'nation', 'count',
              'rating', 'Scent','Longevity', 'Sillage', 'Value for money', 

              'Spring', 'Summer', 'Fall','Winter', 

              'Old', 'Young', 'Men', 'Women', 

              'Leisure', 'Daily','Night Out', 'Business', 'Sport', 'Evening',

              'Earthy', 'Spicy', 'Powdery', 'Fruity','Resinous', 'Leathery', 'Sweet',
              'Oriental', 'Smoky', 'Synthetic', 'Chypre', 'Fougère', 'Animal','Gourmand',
               'Creamy', 'Aquatic', 'Citrus', 'Woody', 'Floral', 'Fresh','Green',

              'gender','year','brand','perfumer','notes',
              'user_id']

CONT_FIELDS = ['user_rating', 'rating']
CONT_FIELDS.extend(types_list)
CONT_FIELDS.extend(['Spring','Summer','Fall','Winter'])
CONT_FIELDS.extend(['Leisure','Daily','Night Out','Business','Sport','Evening'])
CONT_FIELDS.extend(['Old','Young','Men','Women'])
CONT_FIELDS.extend(['Scent','Longevity','Value for money','Sillage'])

CAT_FIELDS = list(set(ALL_FIELDS).difference(CONT_FIELDS))

test_size = 0.2
epochs = 200
embedding_size = 5
lr = 0.002
batch_size = 512