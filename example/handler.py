from src.index import up_mp_init, up_mp_get_urls, up_mp_finalize, up_mp_abort
# 
#                      ,e,
#    /~~~8e  888-~88e   "
#        88b 888  888b 888
#   e88~-888 888  8888 888
#  C888  888 888  888P 888
#   "88_-888 888-_88"  888
#            888

def handler(event, context):
    """
    AWS API Gateway entry point
    """
    path = event['path']
    body = json.loads(event['body'])
    noop = lambda body: {
        'statusCode': 404,
        'body': json.dumps(f"Endpoint {path} Not Found"),
    }
    routes = {
        "/upload/mp-init": up_mp_init,
        "/upload/mp-get-urls": up_mp_get_urls,
        "/upload/mp-finalize": up_mp_finalize,
        "/upload/mp-abort": up_mp_abort,
    }
    method = event['httpMethod']
    if method == 'POST': return routes.get(path, noop)(body)
    return noop
