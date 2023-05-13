import json
import boto3
import logging
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name="us-east-1")
genre_table = dynamodb.Table('genre_predictions')
user_history = dynamodb.Table('user_history')
BUCKET_NAME = 'dataset-bucket'
THUMBNAIL_BUCKET_NAME = 'thumbnails-bucket'
PREVIEW_BUCKET_NAME = 'preview-bucket'

def getgenre_getitem(dominant_genre, filename):
    dynamodb_data = {
        'dominant_genre':dominant_genre,
        'filename':filename
        }
            
    print(dynamodb_data)
    logging.info(dynamodb_data)
    return genre_table.get_item(Key=dynamodb_data)
    


def userhistory_getitem(user_id=" "):
    dynamodb_data = {
        'user_id':user_id,
        }
    logging.info(dynamodb_data)
    return user_history.get_item(Key=dynamodb_data)

def format_response(recommended_filenames, score_dict):
    
    res = []
    for file in recommended_filenames:
        s3 = boto3.client('s3')
        response = s3.head_object(Bucket=BUCKET_NAME, Key=file)
        custom_labels_name = response['Metadata'].get('customlabels-name', 'Featured Title')
        custom_labels_author = response['Metadata'].get('customlabels-author', 'Featured Author')
        
        res.append({
            'dominant_genre': score_dict[file]['dominant_genre'],
            'video_id': file,
            'thumbnail': s3.generate_presigned_url('get_object', Params = {'Bucket': THUMBNAIL_BUCKET_NAME, 'Key': file.split('.')[0] + '-0.jpg'}),
            'preview-url': 'https://' + PREVIEW_BUCKET_NAME + '.s3.amazonaws.com/' + file.split('.')[0] + '.gif',
            'title': custom_labels_name,
            'author': custom_labels_author
        })
    return res
    
def get_trending_songs(table_name, active_song):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    response = table.scan(
        FilterExpression=Key("views").gt(0)
    )
    
    items = response["Items"]
    print("items", items)
    if items:
        sorted_items = sorted(items, key=lambda item: item.get("views"), reverse=True)
        top_songs = sorted_items[1:6]
        
        top_songs_info = {}
        for song in top_songs:
            video_name = song.get("video_name")
            genre = song.get("genre")
            top_songs_info[video_name] = {"dominant_genre": genre}
            
        print("Top trending songs", top_songs_info)
        top_songs_info.pop(active_song, None)
        
        recommended_filenames = list(dict(top_songs_info).keys())
        
        return recommended_filenames, top_songs_info
    else:
        return None, None
    
def lambda_handler(event, context):
    print(event)
    if event.get('active_song'):
        filename = event['active_song']
        dominant_genre = event['active_dominant_genre']
        user_id = event.get('user_id', "5")
    else:
        filename = "imagination.mp4"
        dominant_genre ="rock"
        user_id = "546" # default user
        
    active_song = filename
    response_current = getgenre_getitem(dominant_genre, filename)
    print("response_current", response_current, type(response_current))
    score_dict = {}
    if response_current.get("Item"): 
        print("Yaay I am going to recommend!", response_current)
        user_history_data = userhistory_getitem(user_id)
        genre_prediction_current = json.loads(response_current["Item"]["genre_prediction"])
        genre_prediction_current = genre_prediction_current.get("output") or genre_prediction_current
        response_recommend = genre_table.query(KeyConditionExpression=Key('dominant_genre').eq(dominant_genre))
    
        for j in range(len(response_recommend["Items"])):
            filename = response_recommend["Items"][j]["filename"]
            dominant_genre = response_recommend["Items"][j]["dominant_genre"]
            score = 0
            genre_prediction_recommend = json.loads(response_recommend["Items"][j]["genre_prediction"])
            print(genre_prediction_recommend)
            user_history_data_formatted = json.loads(user_history_data["Item"]["genre_prediction"])
            print("user_history_data_formatted", user_history_data_formatted)
            user_history_data_formatted = user_history_data_formatted.get("output") or user_history_data_formatted
            genre_prediction_recommend = genre_prediction_recommend.get("output") or genre_prediction_recommend
            for i in genre_prediction_current:
                if i in genre_prediction_recommend and i in user_history_data_formatted:
                    diff = genre_prediction_current[i] - genre_prediction_recommend[i]
                    score += int(user_history_data_formatted[i])*diff
                    print(score)
            score_dict[filename] = {"score":score,"dominant_genre":dominant_genre}
            
        print("heyyyyy",score_dict)
        score_dict_sorted = sorted(score_dict.items(), key=lambda x:x[1]['score'])
        score_dict_sorted.pop(next((i for i, item in enumerate(score_dict_sorted) if item[0] == active_song), None))
        recommended_filenames = list(dict(score_dict_sorted).keys())
    else:
        print("Nothing found! Getting trending songs")
        recommended_filenames, score_dict = get_trending_songs("video_history", active_song)
    response = format_response(recommended_filenames, score_dict)
    
    print(response)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'video_list': response})
    }

    
    #print("SCore", score/len(genre_prediction_current))
    #print("genre prediction",genre_prediction_current)
