import boto3
import json
import os
from botocore.client import Config
from botocore.exceptions import ClientError
import mimetypes
import requests

env = os.environ.get('ENVIRONMENT')
local = env == 'local'

AWS_SNS_TOPIC_ARN = os.environ.get('AWS_SNS_TOPIC_ARN')
AWS_S3_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME')
AWS_SNS_EVENT_NAME = os.environ.get('AWS_SNS_EVENT_NAME')


 
"""
tcp_keepalive: bool

Toggles the TCP Keep-Alive socket option used when creating connections. 
By default this value is false; TCP Keepalive will not be used when creating 
connections. To enable TCP Keepalive with the system default configurations, 
set this value to true.
config = Config(
    tcp_keepalive=True
)
def set_connection_header(request, operation_name, **kwargs):
    request.headers['Connection'] = 'keep-alive'
"""

if local:
    AWS_REGION = os.environ.get('AWS_REGION')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    #s3.meta.events.register('request-created.s3.*', set_connection_header)
else:
    s3 = boto3.client('s3')

def up_mp_init(
    body = { 
        "name": "test.mp4", 
        "s3Key": "test" 
    }
):
    """
    initialize multipart upload
    """
    name = body['name']
    s3_path = body['s3Key']
    mime = mimetypes.guess_type(name)[0]
    print(f"initiating multipart upload for {name} with mime type {mime}")
    multipart_params = {
        'Bucket': AWS_S3_BUCKET_NAME,
        'Key': f"{s3_path}/{name}",
        'ContentType': mime,
        #'ACL': 'public-read',
    }
    multipart_upload = s3.create_multipart_upload(**multipart_params) # [1]
    return {
        'statusCode': 200,
        'body': json.dumps({
            'fileId': multipart_upload['UploadId'],
            'fileKey': multipart_upload['Key'],
        }),
    }


def up_mp_get_urls(
    body = { 
        "fileId": "test.mp4", 
        "fileKey": "test", 
        "parts": 1 
    }
):
    """
    get signed urls for each part of the multipart upload
    """
    file_key = body['fileKey']
    file_id = body['fileId']
    parts = body['parts']

    multipart_params = {
        'Bucket': AWS_S3_BUCKET_NAME,
        'Key': file_key,
        'UploadId': file_id,
    }
    signed_urls = []
    
    for index in range(parts):
        signed_urls.append(
            s3.generate_presigned_url(
                'upload_part',
                Params={
                    **multipart_params,
                    'PartNumber': index + 1,
                },
            )
        )
    part_signed_url_list = []
    for index, signed_url in enumerate(signed_urls):
        part_signed_url_list.append({
            'signedUrl': signed_url,
            'PartNumber': index + 1,
        })
    return {
        'statusCode': 200,
        'body': json.dumps({
            'parts': part_signed_url_list,
        }),
    }


def up_mp_finalize(
    body = { 
        "fileId": "test.mp4", 
        "fileKey": "test", 
        "parts": [{ "PartNumber": 1 }] 
    }
):
    """
    finalize multipart upload
    """
    file_id = body['fileId']
    file_key = body['fileKey']
    parts = body['parts']

    multipart_params = {
        'Bucket': AWS_S3_BUCKET_NAME,
        'Key': file_key,
        'UploadId': file_id,
        'MultipartUpload': {
            'Parts': sorted(parts, key=lambda part: part['PartNumber']),
        },
    }
    s3.complete_multipart_upload(**multipart_params)
    message = 'successfully uploaded multi-part file_key: ' + file_key
    print(message)

    # get presigned url to the object and put into sns message
    presigned_url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': AWS_S3_BUCKET_NAME,
            'Key': file_key,
        },
        ExpiresIn= 60 * 60, # 1 hour (seconds)
    )

    response_body = json.dumps({
        'presigned_url': presigned_url,
        'message': message,
    })
    # send sns message
    if local:
        sns = boto3.client(
            'sns',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
    else:
        sns = boto3.client('sns')

    sns.publish(
        TopicArn=AWS_SNS_TOPIC_ARN,
        Message=response_body,
        MessageAttributes = {
            "event_type": {
                "DataType": "String",
                "StringValue": AWS_SNS_EVENT_NAME
            }
        }
    )

    return {
        'statusCode': 200,
        'body': response_body,
    }

def up_mp_abort(
    body = { 
        "fileId": "test.mp4", 
        "fileKey": "test" 
    }
):
    """
    abort multipart upload
    """
    file_id = body['fileId']
    file_key = body['fileKey']

    multipart_params = {
        'Bucket': AWS_S3_BUCKET_NAME,
        'Key': file_key,
        'UploadId': file_id,
    }
    s3.abort_multipart_upload(**multipart_params)
    return {
        'statusCode': 200,
        'body': json.dumps({ 
            "message": f"aborted multi-part file_key: {file_key}"
        }),
    }


#        888 ,e,                            d8
#   e88~\888  "  888-~\  e88~~8e   e88~~\ _d88__
#  d888  888 888 888    d888  88b d888     888
#  8888  888 888 888    8888__888 8888     888
#  Y888  888 888 888    Y888    , Y888     888
#   "88_/888 888 888     "88___/   "88__/  "88_/

def up_mp_turnkey(s3Key, file, name, chunksize = 1024 * 1024 * 5):
    """
    wraps all the steps of the multipart upload process
    into one function (server side only - does the file chunking)
    for calling directly (in process, not via API Gateway)
    """
    init_event_sig = {
        'body': json.dumps({
            'name': name,
            's3Key': s3Key,
        })
    }
    init = up_mp_init(init_event_sig, context=None)
    init_body = json.loads(init['body'])
    fileId = init_body['fileId']
    fileKey = init_body['fileKey']

    # break up the file into chunks
    chunks = []
    file_bytes = file.read(chunksize)
    while file_bytes:
        chunks.append(file_bytes)
        file_bytes = file.read(chunksize)

    urls_event_sig = {
        'body': json.dumps({
            'fileId': fileId,
            'fileKey': fileKey,
            'parts': len(chunks),
        })
    }
    urls = up_mp_get_urls(urls_event_sig, context=None)

    body_parts = json.loads(urls['body'])['parts']
    # parrallelize requests to upload parts
    part_tags = []
    for i in range(chunks):
        # FIXME - need a build step to include non-native lambda packages
        #res = requests.put(body_parts[i]["signedUrl"], data=chunks[i])

        part_tags.append({
            'ETag': res.headers['ETag'],
            'PartNumber': i + 1,
        })

    fin_event_sig = {
        "body": json.dumps({
            "fileId": fileId,
            "fileKey": fileKey,
            "parts": part_tags,
        })
    }
    final_result = up_mp_finalize(fin_event_sig, context=None)
    return final_result['body']


"""
References:

[1]: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/create_multipart_upload.html#

"""