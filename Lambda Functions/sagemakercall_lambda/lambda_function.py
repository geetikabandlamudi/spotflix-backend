import json
import boto3
import logging
import traceback
import json
import boto3
from botocore.config import Config

def lambda_handler(event, context):

    '''
    dynamo = boto3.resource('dynamodb')
    dynamo_table = "genre_predictions"
    genre_table = dynamo.Table(dynamo_table)
    
    filename = "baby.mp4"
    result = {"output": {"rock": 55.55555555555556 , "pop": 44.44444444444444}}
    result = {"output": {"pop": 77.77777777777779,"blues": 5.555555555555555,"rock": 5.555555555555555,"disco":5.555555555555555,"country":5.555555555555555}}
    dominant_genre = list(result["output"].keys())[0]
    
    try:
        logging.info("DynamoDB")
        response_dynamodb = genre_table.put_item(
            Item = {
                'dominant_genre' : str(dominant_genre),
                'filename':str(filename),
                'genre_prediction': json.dumps(result),
              }
            )
        return {
            'statusCode': response_dynamodb,
            'body': json.dumps('Successully uploaded!')
        }
    except:
        logging.info("Error")
        logging.info(traceback.print_exc())
    '''   
    
    config = Config(
        read_timeout=120,
    )
    
    sagemaker_runtime_client = boto3.client('sagemaker-runtime', config=config)
    endpoint_name = "endpoint2023-05-12-16-23-15"
    prompt = "hello"
    payload = {"instances": json.dumps(prompt)}
    body = json.dumps(payload).encode('utf-8')
    print(body)
    
    response = sagemaker_runtime_client.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/json',
        Body=body
    )
    print("Output from sagemaker:: ")
    print(response)
    result = response["Body"].read()
    result = json.loads(result.decode("utf-8"))
    print("Output from sagemaker:: ")
    print(result)
    

    
        
    # sm = boto3.client('sagemaker-runtime')
    # payload = "baby.mp4"

    # response = sm.invoke_endpoint(
    #     EndpointName="pytorch-inference-2023-05-10-05-16-20-201",
    #     ContentType='application/json',
    #     Body=payload
    # )
    # print(response)
    
    # predictions = json.loads(response['Body'].read().decode())
    # print(predictions)
    
    

