from pprint import pprint

import threading
import linecache
import sys

import importlib
from json import dumps, loads, JSONEncoder

from SimpleWebSocketServer import WebSocket
from .parser import BaseParser
from .models import Request, AttackSuccess

from ullyeo.db import Session
from ullyeo.models import Request
from .tmp import request_list


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print ('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))


from sqlalchemy.ext.declarative import DeclarativeMeta
class AlchemyEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return JSONEncoder.default(self, obj)

class BaseHandler(WebSocket):
    def handleMessage(self):
        try:
            request = BaseParser(self.data)

            request_type = request.type
            request_url = request.url
            request_method = request.method
            request_id = request.id

            self.s = Session()
            if request_type == 'Request':
                # do request
                request_body = ''
                try:
                    request_body = str(request.detail['requestBody'])
                except Exception as e:
                    pass
                finally:
                    if request_id in request_list:
                        temp1 = request_list[request_id]
                        temp1 = loads(temp1)
                        temp1['status'] = 1
                        temp1['request_body'] = request_body
                    else:
                        r = Request(1, request_id, request_url, request_method, request_body=request_body)
                        request_list[request_id] = dumps(r, cls=AlchemyEncoder)
            elif request_type == 'SendHeaders':
                # do send headers
                # filter by fuzzing id
                request_headers = ''
                try:
                    request_headers = str(request.detail['requestHeaders'])
                except Exception as e:
                    pass
                finally:
                    if request_id in request_list:
                        temp1 = request_list[request_id]
                        temp1 = loads(temp1)
                        temp1['status'] = 1
                        temp1['request_header'] = request_headers
                        request_list[request_id] = dumps(temp1)
                    else:
                        r = Request(1, request_id, request_url, request_method, request_header=request_headers)
                        request_list[request_id] = dumps(r, cls=AlchemyEncoder)

            elif request_type == 'Received':
                # do received
                # response_headers = request.detail['responseHeaders']
                pass
            elif request_type == 'Body':
                # do body
                pass
            elif request_type == 'Completed':
                # do completed
                response_headers = ''
                try:
                    response_headers = str(request.detail['responseHeaders'])
                except Exception as e:
                    pass
                finally:
                    if request_id in request_list:
                        temp1 = request_list[request_id]
                        temp1 = loads(temp1)
                        temp1['status'] = 1
                        temp1['response_header'] = response_headers
                        request_list[request_id] = dumps(temp1)
                    else:
                        r = Request(1, request_id, request_url, request_method, response_header=response_headers)
                        request_list[request_id] = dumps(r, cls=AlchemyEncoder)

                    th = threading.Thread(target=self.handle_modules, args=(loads(request_list.pop(request_id)),))
                    th.start()
        except Exception as e:
            PrintException()
            exit(0)

    def handle_modules(self, k):
        import config
        module_list = []
        for ml in config.MODULE_LIST:
            tmp = importlib.import_module('modules.'+ml)
            result = tmp.go(k)
            if result:
                print ("good132323")
                r = Request(
                    fuzzing_id=1,
                    request_id=1,
                    url=k['url'],
                    method=k['method'],
                    status=4,
                    request_body=k['request_body'],
                    request_header=k['request_header'],
                    response_header=k['response_header'],
                )
                self.s.add(r)
                w = AttackSuccess(1,1)
                self.s.add(w)
                self.s.commit()
                pass

        # print ("="*20)
        # print (k['url'])
        # print(k['method'])
        # print(k['request_body'])
        # print(k['request_header'])
        # print(k['response_header'])
        return

    def hello(self):
        print ('hello')

    def handleConnected(self):
        print(self.address, 'connected')

    def handleClose(self):
        print(self.address, 'closed')
