import json
import os
# import logging
import requests
from requests_oauthlib import OAuth1Session
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import LambdaFunctionUrlResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.event_handler.exceptions import (
    BadRequestError,
    InternalServerError,
    # NotFoundError,
    # ServiceError,
    UnauthorizedError,
)

logger = Logger()
tracer = Tracer()
app = LambdaFunctionUrlResolver()  # https://awslabs.github.io/aws-lambda-powertools-python/2.9.1/core/event_handler/api_gateway/#lambda-function-url

def get_params(name: str) -> str:
    parameter_extension_endpoint = 'http://localhost:2773/systemsmanager/parameters/get'
    params = {
        'name': name,
        'withDecryption': 'true',
    }
    headers = {
        'X-Aws-Parameters-Secrets-Token': os.getenv('AWS_SESSION_TOKEN'),
    }
    res = requests.get(parameter_extension_endpoint, params=params, headers=headers)
    return json.loads(res.text)['Parameter']['Value']


@app.get('/')
@tracer.capture_method
def get_status():
    return {'status': 'ok'}


@app.post('/')
@tracer.capture_method
def post_tweet():
    if 'api-key' not in app.current_event.headers:
        raise BadRequestError('bad request')
    if app.current_event.headers['api-key'] != get_params('/twitter/api_key'):
        raise UnauthorizedError('unauthorized')
    
    body = json.loads(app.current_event.body)
    if 'message' not in body:
        raise BadRequestError('bad request')
    message = body['message']
    oauth = OAuth1Session(
        client_key            = get_params('/twitter/consumer_key'),
        client_secret         = get_params('/twitter/consumer_secret'),
        resource_owner_key    = get_params('/twitter/access_token'),
        resource_owner_secret = get_params('/twitter/access_token_secret'),
    )
    response = oauth.post(
        url="https://api.twitter.com/1.1/statuses/update.json",
        params={"status": message},
    )

    if response.status_code != 200:
        logger.error(f"Request returned an error: {response.status_code} {response.text}")
        raise InternalServerError('internal server error')
    logger.info(f"Response code: {response.status_code}")
    json_response = response.json()
    logger.debug(json.dumps(json_response, indent=4, sort_keys=True))

    return {'result': 'ok'}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
