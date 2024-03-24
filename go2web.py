#!/usr/bin/env python3
import sys
import socket
import urllib.parse
from bs4 import BeautifulSoup


def make_http_request(url):
    try:
        parsed_url = urllib.urlparse(url)
        with socket.create_connection((parsed_url.netloc, 80)) as s:
            s.sendall(f"GET {parsed_url.path or '/'} HTTP/1.1\r\nHost: {parsed_url.netloc}\r\nConnection: close\r\n\r\n".encode())
            response = b''.join(iter(lambda: s.recv(1024), b''))
        return BeautifulSoup(response, 'html.parser').get_text()
    except Exception as e:
        return f"Error: {e}"

def print_help():
    print("go2web -u <URL>         # make an HTTP request to the specified URL and print the response")
    print("go2web -s <search-term> # make an HTTP request to search the term using Google and print top 10 results")
    print("go2web -h               # show this help")
def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] not in ['-u', '-s', '-h']:
        print_help()
        return

    option, arg = args[:2]
    actions = {'-u': lambda: make_http_request(arg),
               # '-s': lambda: search(arg),
               '-h': print_help}

    print(actions.get(option, lambda: "Invalid option. Use '-h' for help.")())


if __name__ == "__main__":
    main()

