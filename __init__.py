'''
	This file is part of osmdifffetcher.

	osmdifffetcher is free software: you can redistribute it and/or modify
	it under the terms of the GNU Lesser General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	osmdifffetcher is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU Lesser General Public License for more details.

	You should have received a copy of the GNU Lesser General Public License
	along with osmdifffetcher.  If not, see <http://www.gnu.org/licenses/>.

	Copyright 2012 Paul Norman
'''

import sys
import urllib.request, urllib.error, urllib.parse
from datetime import datetime
import time
import os
import errno
import gzip
import io

REPLICATE_BASE = 'http://planet.openstreetmap.org/replication/minute/'

try:
    config = __import__('config.py')
    try:
        if config.REPLICATE_BASE:
            REPLICATE_BASE = config.REPLICATE_BASE
    except:
        pass
except:
    pass
    
opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'OSMDiffFetcher/0.1.0')]
urllib.request.install_opener(opener)

class DiffFetcher:
    def __init__(self, save_state=False):
        self._statef = None
        
        
    def init_state(self):
        '''
        Initalizes with a statefile on disk
        '''
        self._statef = open('state.txt', 'rw+')

        self._process_statefile(self._statef.read())
        
    def save_state(self):
        '''
        Saves the current statefile to disk
        '''
        if self._statef:
            pass
    
    def init_latest(self):
        url = REPLICATE_BASE + 'state.txt'
        statefile = urllib.request.urlopen(url)
        self._process_statefile(statefile)
        
    def _process_statefile(self, statefile):
        state = {}
        for line in statefile:
            if line[0] == '#':
                continue
            k, v = line.split('=', 1)
            state[k] = v.replace('\\:',':').strip()
        self.sequence = int(state['sequenceNumber']) # The sequence number of the next to fetch
    
    @property
    def sequence_path(self):
        '''
        Returns the sequence number as a path (e.g. 123/456/789)
        '''
        sequence_string = str(int(self.sequence)).zfill(9)
        return sequence_string[0:3] + '/' + sequence_string[3:6] + '/' + sequence_string[6:9]
        
    def next_wait(self):
        '''
        Returns the next diff from the server even if it has to wait.
        '''
        result = next(self)
        while not result:
            time.sleep(60.0)
            result = next(self)
        
        return result

    def __next__(self):
        '''
        Returns the next diff from the server or none if up to date
        '''
        url = REPLICATE_BASE + self.sequence_path + '.osc.gz'
        try:
            compressed = urllib.request.urlopen(url)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            else:
                raise e
        self.sequence += 1
        
        return gzip.GzipFile(fileobj=io.StringIO(compressed.read()))
