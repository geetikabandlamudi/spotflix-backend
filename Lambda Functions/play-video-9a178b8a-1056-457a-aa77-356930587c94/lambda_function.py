import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.conditions import Key
from config import BUCKET_NAME
from opensearchpy import OpenSearch, RequestsHttpConnection
from botocore.exceptions import ClientError

OS_INDEX = 'music_data'
def get_video_to_play(key):
    s3 = boto3.client('s3')
    url = s3.generate_presigned_url('get_object', 
                                           Params = {
                                                'Bucket': BUCKET_NAME, 
                                                'Key': key, 
                                                'ResponseContentType': 'video/mp4'
                                           }, 
                                           ExpiresIn = 600)
    
    response = s3.head_object(Bucket=BUCKET_NAME, Key=key)
    print(response)
    custom_labels_name = response['Metadata'].get('customlabels-name', 'Featured Title')
    custom_labels_author = response['Metadata'].get('customlabels-author', 'Featured Author')
    lyrics = os_search_query(key)
    
    return url, custom_labels_name, custom_labels_author, lyrics
    
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
    if not client.indices.exists(OS_INDEX):
        index_resp = client.indices.create(OS_INDEX)
        print("index not present" , index_resp)
    else :
        print("index present")
    return client

def update_user_history(user_id, genre):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('user_history')
   
    response = table.query(KeyConditionExpression= Key('user_id').eq(user_id))
    user_genres = json.loads(response['Items'][0]["genre_prediction"])
    print(user_genres)
    if genre is not None:
        if genre in user_genres:
            user_genres[genre] += 1
        else :
            user_genres[genre] = 1
    
    table.update_item(
        ExpressionAttributeValues={':g': json.dumps(user_genres),},
        Key={'user_id': user_id},
        UpdateExpression="SET genre_prediction = :g",
        ReturnValues="UPDATED_NEW")
    
    
def insert_or_update_record(table_name, key):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    print(key)
    try:
        response = table.update_item(
        Key={'video_name': key['video_name']},
        UpdateExpression="SET #v = #v + :incr",
        ExpressionAttributeNames={"#v": "views"},
        ExpressionAttributeValues={":incr": Decimal(1)},
        ReturnValues="UPDATED_NEW"
    )
    
        # response = table.update_item(
        #     Key=key,
        #     UpdateExpression="SET views = views + :incr",
        #     ExpressionAttributeValues={":incr": Decimal(1)},
        #     ReturnValues="UPDATED_NEW"
        # )
        print("Hii", response)
        
        return response
    except ClientError as e:
        print("Why are you here", e)
        if e.response["Error"]["Code"] == "ValidationException":
            response = table.put_item(
                Item=key
            )
            return response
        else:
            raise e
    
def os_search_query(music_file_name):
    client = os_connection()
    resp = client.search(
    index=OS_INDEX,
    body={
        "query": {
            "match": {
                "video_name": music_file_name
            }
        }
    }
    )
    lyrics=""
    for each_data in resp['hits']['hits']:
        lyrics = each_data['_source']['lyrics']
    print(lyrics)
    return lyrics

def get_video_with_highest_views(table_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    response = table.scan(
        FilterExpression=Key("views").gt(0)
    )
    
    items = response["Items"]
    print("items", items)
    if items:
        highest_views_video = max(items, key=lambda item: item.get("views"))
        video_name = highest_views_video.get("video_name")
        genre = highest_views_video.get("genre")
        print("highest_views_video", highest_views_video)
        return video_name, genre
    else:
        return None, None


def lambda_handler(event, context):
    # TODO implement
    print(event)
    
    if event.get('video-id'):
        key = event['video-id']
        genre = event.get('dominant_genre')
    else:
        key, genre = get_video_with_highest_views("video_history")
    
    key = key or "baby.mp4" 
    genre = genre or "pop"
    user = event.get('user_id', '546') # default user
        
        
    
    update_user_history(user, genre)
    update_val = {"video_name": key, "genre" : genre, "views":1}
    response = insert_or_update_record("video_history", update_val)
    print(response)
    
    url, title, author, lyrics = get_video_to_play(key)
    
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'song_name': key, 
            'url': url, 
            'title': title, 
            'author': author,
            'dominant_genre': genre,
            'lyrics': lyrics
        })
    }
