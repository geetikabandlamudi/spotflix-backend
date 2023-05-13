import json
# import torch
from collections import Counter
# from sklearn.preprocessing import LabelEncoder
import boto3
import librosa
# from model.model import genreNet
# from model.config import MODELPATH, acs_key, acs_sec
# from model.config import GENRES
import flask
import numpy as np
# import json

def lambda_handler(event, context):
    # TODO implement

    acs_key = "key"
    acs_sec = "key"
    
    # Specify the endpoint name that you created while deploying the model
    endpoint_name = '<insert-end-point-here>'
    
    s3_client = boto3.client('s3', aws_access_key_id=acs_key,aws_secret_access_key= acs_sec,region_name="us-east-1")
    # Load the audio file for which you want to make a prediction
    s3_client.download_file("dataset-bucket",'AnotherBrickInTheWall.mp3',"temp.mp4")
    #filename = librosa.ex('trumpet')
    filename = "temp.mp4"
    audio_path = filename
    audio_path = 'path_to_your_audio_file_here'
    
    # Load the data from the audio file
    y, sr = librosa.load(audio_path, mono=True, sr=22050)
    S = librosa.feature.melspectrogram(y=y, sr=sr).T
    S = S[:-1 * (S.shape[0] % 128)]
    num_chunk = S.shape[0] / 128
    data_chunks = np.split(S, num_chunk)
    
    # Create a connection to the SageMaker runtime
    runtime = boto3.Session().client('sagemaker-runtime')
    
    # Loop through each chunk of data and get the predicted genre
    genres = []
    # for i, data in enumerate(data_chunks):
        # Convert the data to a JSON string
    data = data_chunks[0]
    data_str = json.dumps(data.tolist())
    
    # Make the prediction request to the endpoint
    response = runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/json',
        Body=data_str)
    
    # Parse the response from the endpoint
    result = json.loads(response['Body'].read().decode())
    pred_index = int(result['predictions'][0]['predicted_genre'])
    pred_genre = GENRES[pred_index]
    genres.append(pred_genre)
    
    # Get the most likely genre and its confidence
    counts = np.bincount([GENRES.index(g) for g in genres])
    max_count_index = np.argmax(counts)
    max_count = counts[max_count_index]
    confidence = max_count / len(genres)
    most_likely_genre = GENRES[max_count_index]

    return {
        'statusCode': 200,
        'body': json.dumps(most_likely_genre)
    }
