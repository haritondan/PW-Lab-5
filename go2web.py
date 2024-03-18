#!/usr/bin/env python3
import sys
import socket
import urllib.parse
from html.parser import HTMLParser

class GoogleSearchParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_search_result = False
        self.search_results = []
        self.current_result = ""
        self.result_count = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'h3' and ('class', 'tTf9Te') in attrs:
            self.in_search_result = True

    def handle_endtag(self, tag):
        if tag == 'h3' and self.in_search_result:
            self.in_search_result = False
            self.result_count += 1
            self.search_results.append(self.current_result)
            self.current_result = ""

    def handle_data(self, data):
        if self.in_search_result:
            self.current_result += data + "\n"

def make_http_request(url):
    parsed_url = urllib.parse.urlparse(url)
    host = parsed_url.netloc
    path = parsed_url.path if parsed_url.path else '/'
    try:
        with socket.create_connection((host, 80)) as sock:
            sock.sendall(f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())
            response = b''
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                response += data
    except socket.error as e:
        print(f"Error: {e}")
        return None
    return response.decode(errors='ignore')

def print_help():
    print("Usage:")
    print("go2web -u <URL>         # make an HTTP request to the specified URL and print the response")
    print("go2web -s <search-term> # make an HTTP request to search the term using Google and print top 10 results")
    print("go2web -h               # show this help")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or '-h' in args:
        print_help()
    elif '-u' in args:
        try:
            url_index = args.index('-u') + 1
            url = args[url_index]
            response = make_http_request(url)
            if response:
                print(response)
        except IndexError:
            print("Error: Missing URL after -u")
        except IndexError:
            print("Error: Missing search term after -s")

