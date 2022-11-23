from model import DeepFM
import numpy as np
import pandas as pd
from time import perf_counter
import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow.keras.metrics import BinaryAccuracy, AUC
import pandas as pd
import config
import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow.keras.metrics import BinaryAccuracy, AUC
from sklearn.preprocessing import MinMaxScaler
import pickle
from tensorflow import keras

def train_on_batch(model, optimizer, acc, auc, inputs, targets):
    with tf.GradientTape() as tape:
        y_pred = model(inputs)
        loss = tf.keras.losses.binary_crossentropy(from_logits=False, y_true=targets, y_pred=y_pred)

    grads = tape.gradient(target=loss, sources=model.trainable_variables)

    # apply_gradients()를 통해 processed gradients를 적용함
    optimizer.apply_gradients(zip(grads, model.trainable_variables))

    # accuracy & auc
    acc.update_state(targets, y_pred)
    auc.update_state(targets, y_pred)

    return loss

def get_data(item_table_path, rating_table_path, notes_info_path, ALL_FIELDS , CAT_FIELDS, CONT_FIELDS, test_size):
    item_table = pd.read_csv(item_table_path, encoding ='utf-8-sig')
    rating_table = pd.read_csv(rating_table_path, encoding ='utf-8-sig')
    notes_info =  pd.read_csv(notes_info_path,index_col=[0,1])
    X, Y, field_dict, field_index = preprocessing(item_table, rating_table, notes_info, ALL_FIELDS , CAT_FIELDS, CONT_FIELDS)
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=test_size, stratify=Y)
    return X_train, X_test, Y_train, Y_test



# 반복 학습 함수
def train(item_table_path, rating_table_path, notes_info_path, ALL_FIELDS , CAT_FIELDS, CONT_FIELDS, test_size, epochs, embedding_size, lr, batch_size):
    best_auc = 0
    train_ds, test_ds, field_dict, field_index = get_data(item_table_path, rating_table_path, notes_info_path, ALL_FIELDS , CAT_FIELDS, CONT_FIELDS, test_size)

    model = DeepFM(embedding_size=embedding_size, num_feature=len(field_index),
                   num_field=len(field_dict), field_index=field_index)

    optimizer = tf.keras.optimizers.Adam(learning_rate=lr)

    print("Start Training: Batch Size: {}, Embedding Size: {}".format(batch_size, embedding_size))
    start = perf_counter()
    for i in range(epochs):
        acc = BinaryAccuracy(threshold=0.5)
        auc = AUC()
        loss_history = []

        for x, y in train_ds:
            loss = train_on_batch(model, optimizer, acc, auc, x, y)
            loss_history.append(loss)

        print("Epoch {:03d}: 누적 Loss: {:.4f}, Acc: {:.4f}, AUC: {:.4f}".format(
            i, np.mean(loss_history), acc.result().numpy(), auc.result().numpy()))

    test_acc = BinaryAccuracy(threshold=0.5)
    test_auc = AUC()
    for x, y in test_ds:
        y_pred = model(x)
        test_acc.update_state(y, y_pred)
        test_auc.update_state(y, y_pred)
    result_acc = test_acc.result().numpy()
    result_auc = test_auc.result().numpy()
    if result_auc > best_auc:
        best_auc = result_acc
        model.save_weights('/home/dhkim/Fragrance/model/best_model_epoch({})_batch({})_embedding({}).h5'.format(epochs, batch_size, embedding_size))
    print("테스트 ACC: {:.4f}, AUC: {:.4f}".format(result_acc ,result_auc))
    print("Batch Size: {}, Embedding Size: {}".format(batch_size, embedding_size))
    print("걸린 시간: {:.3f}".format(perf_counter() - start))
    #model.save_weights('/home/dhkim/Fragrance/model/weights_epoch({})_batch({})_embedding({}).h5'.format(epochs, batch_size, embedding_size))


 
if __name__ == '__main__':
    item_table_path = config.item_table_path
    rating_table_path = config.rating_table_path
    notes_info_path = config.notes_info_path
    types_list = config.types_list
    ALL_FIELDS = config.ALL_FIELDS
    types_dict = config.types_dict
    test_size = config.test_size 
    epochs = config.epochs
    embedding_size = config.embedding_size
    lr = config.lr
    batch_size = config.batch_size
    X = pd.read_csv('/home/dhkim/Fragrance/data/X.csv', encoding ='utf-8-sig')
    Y = pd.read_csv('/home/dhkim/Fragrance/data/Y.csv', encoding ='utf-8-sig')

    with open("/home/dhkim/Fragrance/data/field_dict.pkl", 'rb') as f:
        field_dict = pickle.load(f)
    with open("/home/dhkim/Fragrance/data/field_index.pkl", 'rb') as f:
        field_index = pickle.load(f)

    gpu = tf.config.experimental.list_physical_devices('GPU')
    if gpu:
        try:
            for i in gpu:
                tf.config.experimental.set_memory_growth(i, True)
        except RuntimeError as e:
            print(e)

    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=test_size, stratify=Y)

    model = DeepFM(embedding_size=11, num_feature=len(field_index),
                    num_field=len(field_dict), field_index=field_index)

    optimizer = keras.optimizers.Adam(lr=lr)

    model.compile(loss='binary_crossentropy', optimizer=optimizer, metrics=[tf.keras.metrics.BinaryAccuracy()])
    model.fit(X_train, Y_train, epochs=100, verbose=1, validation_split=0.4, shuffle=True, batch_size=512)