#!/usr/bin/env python

import json, urlparse, sys, os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from subprocess import call

class GitLabPostReceive(BaseHTTPRequestHandler):

    CONFIG_FILEPATH = './gitlabpost-receive.json'
    config = None
    quiet = False
    daemon = False

    @classmethod
    def getConfig(myClass):
        if(myClass.config == None):
            try:
                configString = open(myClass.CONFIG_FILEPATH).read()
            except:
                sys.exit('Could not load ' + myClass.CONFIG_FILEPATH + ' file')

            try:
                myClass.config = json.loads(configString)
            except:
                sys.exit(myClass.CONFIG_FILEPATH + ' file is not valid json')

            for repository in myClass.config['repositories']:
                if(not os.path.isdir(repository['path'])):
                    sys.exit('Directory ' + repository['path'] + ' not found')
                if(not os.path.isdir(repository['path'] + '/.git')):
                    sys.exit('Directory ' + repository['path'] + ' is not a Git repository')

        return myClass.config

    def do_POST(self):
        paths = self.getMatchingPaths(self.parseRequest())
        for path in paths:
            self.pull(path)

    def parseRequest(self):
        length = int(self.headers.getheader('content-length'))
        body = self.rfile.read(length)
        post = json.loads(body)
        items = {'url': post['repository']['url'], 'ref': post['ref']}
        return items

    def getMatchingPaths(self, items):
        res = []
        config = self.getConfig()
        for repository in config['repositories']:
            if(repository['url'] == items['url'] and repository['ref'] == items['ref']):
                res.append(repository['path'])
        return res

    def respond(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('<html><body><p>OK</p></body></html>')

    def pull(self, path):
        if(not self.quiet):
            print "\nPost push request received"
            print 'Updating ' + path
        call(['cd "' + path + '" && git pull'], shell=True)
        self.respond()

def main():
    try:
        server = None
        for arg in sys.argv:
            if(arg == '-d' or arg == '--daemon-mode'):
                GitLabPostReceive.daemon = True
                GitLabPostReceive.quiet = True
            if(arg == '-q' or arg == '--quiet'):
                GitLabPostReceive.quiet = True

        if(GitLabPostReceive.daemon):
            pid = os.fork()
            if(pid != 0):
                sys.exit()
            os.setsid()

        if(not GitLabPostReceive.quiet):
            print 'Gitlab PostReceive Service v 0.1 started'
        else:
            print 'Gitlab PostReceive Service v 0.1 started in daemon mode'

        server = HTTPServer(('', GitLabPostReceive.getConfig()['port']), GitLabPostReceive)
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit) as e:
        if(e): # wtf, why is this creating a new line?
            print >> sys.stderr, e

        if(not server is None):
            server.socket.close()

        if(not GitLabPostReceive.quiet):
            print 'Goodbye'

if __name__ == '__main__':
    main()
