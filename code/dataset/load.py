
import pickle
import natsort

def get_data():
    # load
    with open('/private/sogang_fragrance/assets/pkl/field_dict.pkl', 'rb') as f:
        field_dict = pickle.load(f)

    with open('/private/sogang_fragrance/assets/pkl/field_index.pkl', 'rb') as f:
        field_index = pickle.load(f)

    with open('/private/sogang_fragrance/assets/pkl/test_Y.pkl', 'rb') as f:
        test_Y = pickle.load(f)

    with open('/private/sogang_fragrance/assets/pkl/train_X.pkl', 'rb') as f:
        train_X = pickle.load(f)

    return field_dict, field_index, test_Y, train_X

if __name__ == '__main__':
    field_dict, field_index, test_Y, train_X = get_data()

    print('field_dict\n', field_dict, '\n')
    print('field_index\n', field_index, '\n')
    print('test_Y\n', test_Y, '\n')
    print('train_X\n', train_X, '\n')
    print(train_X['Earthynotes'])

    for (k, v) in field_dict.items():
        print(k, v)