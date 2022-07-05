import os
import json


class Config(object):
    '''config for debug server'''

    def __init__(self, host='localhost', port=5677):
        self.host = host
        self.port = port

    def save(self, path):
        '''save config to file'''
        with open(path, 'w') as f:
            json.dump(self.__dict__, f)

    def load(self, path):
        '''load config from file'''
        with open(path, 'r') as f:
            config = json.load(f)
        self.__dict__.update(config)

    @staticmethod
    def from_file(path):
        '''load config from file'''
        with open(path, 'r') as f:
            config = json.load(f)
        return Config(**config)