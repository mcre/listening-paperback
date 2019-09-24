import os

import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


def youtube():
    flow = flow_from_clientsecrets('./certs/youtube_client_secrets.json', scope='https://www.googleapis.com/auth/youtube.readonly')

    storage = Storage(f'{os.environ["HOME"]}/.youtube-upload-credentials.json')
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        flags = argparser.parse_args()
        credentials = run_flow(flow, storage, flags)
    return build('youtube', 'v3', http=credentials.authorize(httplib2.Http()))