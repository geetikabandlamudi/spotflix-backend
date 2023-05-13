import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection

OS_INDEX = 'music_data'
BUCKET_NAME = 'dataset-bucket'
THUMBNAIL_BUCKET_NAME = 'thumbnails-bucket'
PREVIEW_BUCKET_NAME = 'preview-bucket'

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

def format_response(searched_filenames):
    
    res = []
    for file in searched_filenames:
        s3 = boto3.client('s3')
        print(file)
        response = s3.head_object(Bucket=BUCKET_NAME, Key=file)
        print(response)
        custom_labels_name = response['Metadata'].get('customlabels-name', 'Featured Title')
        custom_labels_author = response['Metadata'].get('customlabels-author', 'Featured Author')
        
        res.append({
            'dominant_genre': 'pop',
            'video_id': file,
            'thumbnail': s3.generate_presigned_url('get_object', Params = {'Bucket': THUMBNAIL_BUCKET_NAME, 'Key': file.split('.')[0] + '-0.jpg'}),
            'preview-url': 'https://' + PREVIEW_BUCKET_NAME + '.s3.amazonaws.com/' + file.split('.')[0] + '.gif',
            'title': custom_labels_name,
            'author': custom_labels_author
        })
    return res
    

def os_search_query(search_text):
    client = os_connection()
    resp = client.search(
    index=OS_INDEX,
    body={
        "query": {
            "query_string": {
                "query": search_text
            }
        }
    }
    )
    print(resp)
    return resp

def lambda_handler(event, context):
    # TODO implement
    
    key = event['searched_text']
    
    resp = os_search_query(key)
    music_list=set()
    for each_data in resp['hits']['hits']:
        #print(each_data)
        video_name = each_data['_source']['video_name'] 
        music_list.add(video_name)
    
    print(music_list)
        
    
    #searched_filenames = ['baby.mp4', 'darkside.mp4']
    response = format_response(music_list)
    return {
        'statusCode': 200,
        'body': json.dumps({'video_list': response})
    }
