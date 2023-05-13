import json
import os
import torch
import torch.nn.functional as F
from torch.nn import Module, Conv2d, MaxPool2d, Linear, Dropout, BatchNorm2d

import numpy as np
import librosa
from sklearn.preprocessing import LabelEncoder
from collections import Counter
import logging
import random

GENRES = ['blues', 'classical', 'country', 'disco', 'hiphop', 'jazz', 'metal', 'pop', 'reggae', 'rock']
audio_wavs = ['brahms', 'humpback', 'fishin', 'choice', 'nutcracker', 'pistachio', 'robin', 'sweetwaltz', 'vibeace']

class genreNet(Module):
    def __init__(self):
        super(genreNet, self).__init__()

        self.conv1 = Conv2d(in_channels=1, out_channels=64, kernel_size=3, stride=1, padding=1)
        torch.nn.init.xavier_uniform(self.conv1.weight)
        self.bn1 = BatchNorm2d(64)
        self.pool1 = MaxPool2d(kernel_size=2)

        self.conv2 = Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1)
        torch.nn.init.xavier_uniform(self.conv2.weight)
        self.bn2 = BatchNorm2d(128)
        self.pool2 = MaxPool2d(kernel_size=2)

        self.conv3 = Conv2d(in_channels=128, out_channels=256, kernel_size=3, stride=1, padding=1)
        torch.nn.init.xavier_uniform(self.conv3.weight)
        self.bn3 = BatchNorm2d(256)
        self.pool3 = MaxPool2d(kernel_size=4)

        self.conv4 = Conv2d(in_channels=256, out_channels=512, kernel_size=3, stride=1, padding=1)
        torch.nn.init.xavier_uniform(self.conv4.weight)
        self.bn4 = BatchNorm2d(512)
        self.pool4 = MaxPool2d(kernel_size=4)

        self.fc1 = Linear(in_features=2048,  out_features=1024)
        self.drop1 = Dropout(0.5)

        self.fc2 = Linear(in_features=1024,  out_features=256)
        self.drop2 = Dropout(0.5)

        self.fc3 = Linear(in_features=256,   out_features=10)

    def forward(self, inp):
        x = F.relu(self.bn1(self.conv1(inp)))
        x = self.pool1(x)
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        x = F.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)
        x = F.relu(self.bn4(self.conv4(x)))
        x = self.pool4(x)
        x = x.view(x.size()[0], -1)
        x = F.relu(self.fc1(x))
        x = self.drop1(x)
        x = F.relu(self.fc2(x))
        x = self.drop2(x)
        x = F.log_softmax(self.fc3(x))
        return x


def model_fn(model_dir):
    model_path = os.path.join(model_dir, 'net.pt')
    net = genreNet()
    net.load_state_dict(torch.load(model_path, map_location='cpu'))
    logging.info('Model Loaded')
    return net


def input_fn(request_body, content_type="application/json"):
    logging.info(request_body)
    logging.info(content_type)
    logging.info("Entered input fn")
    if content_type == "application/json":
        request = json.loads(request_body)
    else:
        request = request_body
    return request


def predict_fn(audio_path, model):
    logging.info('splitting into chunks')
    try:
        logging.info('entered try')
        y, sr = librosa.load(audio_path, mono=True, sr=22050)
        logging.info('librosa song loaded from s3')
    except Exception as ex:
        logging.info('entered exception')
        logging.info(ex)
        random_val = random.choice(audio_wavs)
        logging.info(random_val)
        logging.info('done')
        filename = librosa.ex(random_val)
        y, sr = librosa.load(filename)
        logging.info('loading file')
    S = librosa.feature.melspectrogram(y=y, sr=sr).T
    S = S[:-1 * (S.shape[0] % 128)]
    num_chunk = S.shape[0] / 128
    data_chunks = np.split(S, num_chunk)
    genres = list()
    le = LabelEncoder().fit(GENRES)
    logging.info('entering for loop for genre prediction')
    for i, data in enumerate(data_chunks):
        data = torch.FloatTensor(data).view(1, 1, 128, 128)
        preds = model(data)
        pred_val, pred_index = preds.max(1)
        pred_index = pred_index.data.numpy()
        pred_val = np.exp(pred_val.data.numpy()[0])
        pred_genre = le.inverse_transform(pred_index).item()
        if pred_val >= 0.5:
            genres.append(pred_genre)
    # ------------------------------- #
    logging.info("final counting")
    s = float(sum([v for k, v in dict(Counter(genres)).items()]))
    pos_genre = sorted([(k, v/s*100) for k, v in dict(Counter(genres)).items()], key=lambda x:x[1], reverse=True)
    print("successfully calculated")
    pos_genre_dict = {}
    for i in pos_genre:
        pos_genre_dict[i[0]] = i[1]
    #pos_genre_dict_dumps = json.dumps(pos_genre_dict)
    logging.info("added")
    logging.info(pos_genre_dict)
    prediction_output = pos_genre_dict
    return prediction_output


def output_fn(prediction_output, accept="application/json"):
    if accept == "application/json":
        try:
            logging.info("returned successfully")
            print("return successfully")
            result = {"output": prediction_output}
            logging.info(result)
            return result
        except Exception as ex:
            logging.info("DUmps")
            logging.info(ex)
            return json.dumps(result)
    else:
        return json.dumps(result)



