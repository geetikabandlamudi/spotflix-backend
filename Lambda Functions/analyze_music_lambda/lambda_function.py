import json
import boto3
import uuid
import time
import urllib
import random
from botocore.config import Config
from opensearchpy import OpenSearch, RequestsHttpConnection



BUCKET_NAME = 'dataset-bucket'
OS_INDEX = 'music_data'

# GENRES =  [ 'blues',
#             'classical',
#             'country',
#             'disco',
#             'hiphop',
#             'jazz',
#             'metal',
#             'pop',
#             'reggae',
#             'rock'  ]


def predict_genre(filename):
    
    # # Insert into genre_predictions
    # result = {}
    # num_genres = random.randint(1, len(GENRES))  # Number of genres to include in the dictionary

    # selected_genres = random.sample(GENRES, num_genres)  # Select a random subset of genres
    
    # total_value = 0  # Sum of all values
    
    # for genre in selected_genres:
    #     random_value = round(random.uniform(0, 1), 10)
    #     result[genre] = random_value
    #     total_value += random_value

    # # Normalize the values
    # for genre in result:
    #     result[genre] = (result[genre] / total_value) * 100
    
    # Sagemaker call
    config = Config(read_timeout=120,)
    sagemaker_runtime_client = boto3.client('sagemaker-runtime', config=config)
    endpoint_name = "<endpoint-here>"
    payload = {"instances": json.dumps(filename)}
    body = json.dumps(payload).encode('utf-8')
    
    response = sagemaker_runtime_client.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/json',
        Body=body
    )
    print("Output from sagemaker:: ")
    print(response)
    result = response["Body"].read()
    result = json.loads(result.decode("utf-8"))
    print(result)
    result = result.get("output", {})
    print("Output from sagemaker:: ")
    print(result)
    if result:
        dominant_genre = max_key = max(result, key=lambda k: result[k])
    else:
        print("Could not predict the genre")
        dominant_genre = "pop"
    
    # Insert into dynamodb
    dynamo = boto3.resource('dynamodb')
    dynamo_table = "genre_predictions"
    genre_table = dynamo.Table(dynamo_table)
    response_dynamodb = genre_table.put_item(
            Item = {
                'dominant_genre' : str(dominant_genre),
                'filename':str(filename),
                'genre_prediction': json.dumps(result),
              }
            )
    return dominant_genre, result.keys()
    
    
    
def lambda_handler(event, context):
    # TODO implement

    print(event);
    music_file_name = event['Records'][0]['messageAttributes']['video-name']['stringValue']
    dominant_genre, predicted_genre = predict_genre(music_file_name)
    
    s3 = boto3.client('s3')
    response = s3.head_object(Bucket=BUCKET_NAME, Key=music_file_name)
    custom_labels_name = response['Metadata'].get('customlabels-name', 'Featured Title')
    custom_labels_author = response['Metadata'].get('customlabels-author', 'Featured Author')
    #print("labels" + custom_labels_name + " " + custom_labels_author)
    
    dominant_genre = "pop"
    predicted_genre = ['pop', 'rock', 'jazz']
    
    
    
    lyrics = get_lyrics_using_transcribe(music_file_name)
    client = os_connection()
    data = {
        "video_name" : music_file_name,
        "video_title": custom_labels_name.lower(),
        "Author" : custom_labels_author.lower(),
        'dominant_genre' : dominant_genre.lower(),
        "predicted_genre":predicted_genre, # have to make sure  this is all lowercase values
        "lyrics" : lyrics
    }
    
    resp = client.index(OS_INDEX, body=data)
    print(resp)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }


def os_connection():
    host = "search-music-data-5idrxdn22l7tvdfrryyhb7ugla.us-east-1.es.amazonaws.com"
    port = 443
    auth = ("violetorigin", "Blueorigin1!")
    
    client = OpenSearch(
        hosts = [{"host": host, "port": port}],
        http_auth = auth,
        use_ssl = True,
        verify_certs = True,
        ssl_assert_hostname = False,
        ssl_show_warn = False,
        connection_class = RequestsHttpConnection
    )
    print(client)
    if not client.indices.exists(OS_INDEX):
        index_resp = client.indices.create(OS_INDEX)
        print("index not present" , index_resp)
    else :
        print("index present")
    return client

def get_lyrics_using_transcribe(video_file_name):
    print(video_file_name)
    s3Path = "s3://" + BUCKET_NAME + "/" + video_file_name
    jobName = video_file_name + '-' + str(uuid.uuid4())
    
    client = boto3.client('transcribe')
    response = client.start_transcription_job(
        TranscriptionJobName=jobName,
        LanguageCode='en-US',
        MediaFormat='mp4',
        Media={
            'MediaFileUri': s3Path
        }
    )
    
    while True:
        result = client.get_transcription_job(TranscriptionJobName=jobName)
        if result['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        time.sleep(15)
        print("status" + result['TranscriptionJob']['TranscriptionJobStatus'])
    if result['TranscriptionJob']['TranscriptionJobStatus'] == "COMPLETED":
        result = client.get_transcription_job(TranscriptionJobName=jobName)
        print(result)
        uri = result['TranscriptionJob']['Transcript']['TranscriptFileUri']
        content = urllib.request.urlopen(uri).read().decode('UTF-8')
        data =  json.loads(content)
        transcribed_text = data['results']['transcripts'][0]['transcript']
        print(transcribed_text)
        return transcribed_text
    return ""
    #print("status" + result['TranscriptionJob']['TranscriptionJobStatus'])
