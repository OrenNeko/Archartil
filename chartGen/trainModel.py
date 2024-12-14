import os.path

import numpy
import numpy as np
from keras.layers import Conv2D, LSTM, Dense, MaxPooling2D, MaxPooling1D, Flatten, Reshape
from keras.saving.save import load_model
from sklearn.model_selection import KFold

import chartGen.util as util
from chartGen.genHandler.musicHandler import MusicHandler
from chartGen.genHandler.affHandler import AffHandler
from keras.models import Sequential


def times_to_label(musicHandler, affHandler):
    label_length = round(musicHandler.duration * 1000 / interval)
    label_array = np.zeros(label_length)
    for t in affHandler.onset_times:
        label_position = round(t / interval)
        # 标准正态分布
        label_array[label_position] = max(1, label_array[label_position])
        label_array[label_position + 1] = max(0.9974, label_array[label_position + 1])
        label_array[label_position - 1] = max(0.9974, label_array[label_position - 1])
        label_array[label_position + 2] = max(0.9545, label_array[label_position + 2])
        label_array[label_position - 2] = max(0.9545, label_array[label_position - 2])
        label_array[label_position + 3] = max(0.6827, label_array[label_position + 3])
        label_array[label_position - 3] = max(0.6827, label_array[label_position - 3])
        label_array[label_position + 4] = max(0.383, label_array[label_position + 3])
        label_array[label_position - 4] = max(0.383, label_array[label_position - 3])

    print(np.count_nonzero(label_array))

    return label_array


def train(feature, label):
    model = Sequential()
    model.add(Conv2D(filters=7, kernel_size=(3, 3), data_format="channels_last", activation="relu", input_shape=(15, 80, 3)))
    model.add(MaxPooling2D(pool_size=(1, 3)))
    model.add(Conv2D(filters=10, kernel_size=(3, 3), data_format="channels_last", activation="relu", input_shape=(9, 26, 10)))
    model.add(MaxPooling2D(pool_size=(1, 3)))
    model.add(Reshape(target_shape=(11, 80)))
    model.add(LSTM(200, activation="tanh"))
    model.add(Reshape(target_shape=(5, 40)))
    model.add(LSTM(200, activation="tanh"))
    model.add(Dense(256, activation="relu"))
    model.add(Dense(128, activation="relu"))
    model.add(Dense(1, activation="relu"))
    model.summary()

    model.compile(loss='mse',
                  optimizer='adam',
                  metrics=['accuracy'])

    kf = KFold(n_splits=3, shuffle=True, random_state=100)
    for train_index, test_index in kf.split(feature, label):
        x_train, x_test, y_train, y_test = feature[train_index], feature[test_index], label[train_index], label[test_index]

        model.fit(x_train, y_train,
                  batch_size=300,
                  epochs=5,
                  validation_data=(x_test, y_test))

    model.save("firstModel.h5")

    return model


def predict(model_name, input_feature):
    model = load_model(model_name)
    predict_result = model.predict(input_feature)
    output = []
    print(numpy.sum(predict_result))
    for time_id, i in enumerate(predict_result):
        if i[0] > 0.95:
            print(time_id * interval)
            output.append(time_id * interval)

    print(output)
    return output


base_path = "../chart/bookmaker"
test_aff = AffHandler(aff_file=os.path.join(base_path, "2.aff"))
# 计算训练数据的端点作为标签
test_aff.get_onset_times()
# 计算合适的interval
interval = 60000 / test_aff.bpm
while interval > 32:
    interval = interval / 4
interval = round(interval)
print("Interval:", interval)
# 读取时减去offset，整个计算过程不考虑offset
test_music = MusicHandler(music_file=os.path.join(base_path, "base.wav"), offset=test_aff.offset / 1000)
# 提取特征与标签
features = test_music.extract_feature(frame_interval=interval)
labels = times_to_label(test_music, test_aff)
print("Feature Shape:", features.shape)
# 训练模型
# m = train(features, labels)
# 预测结果
time_list = predict("firstModel.h5", features)
# 输出结果
afflist = util.times_to_aff(time_list)
# 添加删去的偏置offset，保存
util.save_afflist(os.path.join(base_path, "3.aff"), afflist, offset=test_aff.offset, bpm=test_aff.bpm)
