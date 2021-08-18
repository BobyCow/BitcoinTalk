import requests
import socket
import json

def make_request(url, verbose=1, prefix=''):
   ## Making request ##
   local_addr = socket.gethostbyname(socket.gethostname())
   headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
   response = requests.get(url=url, headers=headers, timeout=100)
   ## Displaying result ##
   if verbose:
      print(f'{prefix}[{response.status_code}] <{response.reason}> -- {response.url} FROM {local_addr}')
   return response

## Display all attributes of an object and their values ##
def dump(obj):
   for attr in dir(obj):
      print('obj.%s = %r' % (attr, getattr(obj, attr)))

## Pretty display of a dictionnary ##
def pretty(d, indent=0):
   for key, value in d.items():
      print(' ' * indent + f'{str(key)}:')
      if isinstance(value, dict):
         pretty(value, indent + 4)
      else:
         print(' ' * (indent + 4) + str(value))

def get_pool_names(filename='WORDS/pools.json'):
    with open(filename, 'r') as file:
        return [name.lower() for name in json.load(file)['names']]