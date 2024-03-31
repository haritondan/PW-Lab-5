import json
import ssl
import sys
import socket
from urllib.parse import urlparse
from bs4 import BeautifulSoup

PORT = 80
RECV_SIZE = 4096

def make_http_request(url):
    try:
        if url.startswith('http://'):
            url = url[len('http://'):]
        elif url.startswith('https://'):
            url = url[len('https://'):]

        parts = url.split('/', 1)
        host = parts[0]
        path = '/'

        if len(parts) > 1:
            path = '/' + parts[1]

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, PORT))
        request = f"GET {path} HTTP/1.1\r\nHost:{host}\r\nConnection: close\r\n\r\n"

        client.sendall(request.encode("utf-8"))

        response = b""
        while True:
            chunk = client.recv(RECV_SIZE)
            if not chunk:
                break
            response += chunk

        client.close()

        soup = BeautifulSoup(response, 'html.parser')
        redirect_codes = ["HTTP/1.1 301", "HTTP/1.1 302", "HTTP/1.1 303", "HTTP/1.1 307", "HTTP/1.1 308"]

        if any(soup.decode().startswith(code) for code in redirect_codes):

            print("Redirecting...\n")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ssl_socket = ssl.wrap_socket(client_socket, ssl_version=ssl.PROTOCOL_TLS)
            ssl_socket.connect((host, 443))
            ssl_socket.sendall(request.encode("utf-8"))

            response = b''
            while True:
                data = ssl_socket.recv(1024)
                if not data:
                    break
                response += data

            ssl_socket.close()

        return response

    except socket.error as e:
        print("Error making request:", e)
        sys.exit(1)


def search(response):
    headers, body = response.split(b'\r\n\r\n', 1)
    content_type = None
    for header in headers.split(b'\r\n'):
        if header.startswith(b'Content-Type:'):
            content_type = header.split(b':', 1)[1].strip()

    if content_type and content_type.startswith(b'application/json'):
        print("\nJSON Response Headers:\n")
        print(headers.decode('utf-8'))

        print("\nJSON Response Body:\n")
        try:
            json_obj = json.loads(body.decode('utf-8'))
            print(json.dumps(json_obj, indent=4))
        except json.JSONDecodeError as e:
            print("Error decoding JSON response:", e)

    elif content_type and content_type.startswith(b'text/html'):
        soup = BeautifulSoup(response, 'html.parser')

        print("\nHTTP Response:\n")
        for line in soup.get_text().splitlines():
            if (line.startswith("Transfer-Encoding:")):
                print(line)
                break
            else:
                print(line)

        # Define tags to extract
        tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'ul']

        print("\nExtracted content: \n")
        for tag in soup.find_all(tags):
            if tag.name.startswith('h'):
                print(tag.get_text().strip() + "\n")
            elif tag.name == 'ul':
                for li in tag.find_all('li'):
                    print(li.get_text().strip())
            elif tag.name == 'a' and tag.get('href') and (
                    tag.get('href').startswith('http://') or tag.get('href').startswith('https://')):
                print(tag.get_text().strip())
                print("Link:", tag.get('href'))
            elif tag.name == 'p':
                print(tag.get_text().strip())
    else:
        print("\nResponse not supported. Try another URL.\n")
    print()


def print_search(response):
    soup = BeautifulSoup(response, 'html.parser')
    results = soup.find_all('li', class_='b_algo')

    print("\n Top 10 search results: \n")
    for i, result in enumerate(results):
        title = result.find('h2').get_text()
        url = result.find('a')['href']
        print(f"{i + 1}. {title} - {url} \n")


def main():
    if len(sys.argv) == 1 or sys.argv[1] == "-h":
        print("Usage:")
        print("go2web -u <URL>         # make an HTTP request to the specified URL and print the response")
        print(
            "go2web -s <search-term> # make an HTTP request to search the term using your favorite search engine and print top 10 results")
        print("go2web -h               # show this help")
        sys.exit(0)

    if sys.argv[1] == "-u" and len(sys.argv) <= 3:
        if len(sys.argv) != 3:
            print("Usage: go2web -u <URL>")
            sys.exit(1)
        url = sys.argv[2]
        cache_data = load_cache(cache_file)

        if cache_data.get(url):
            print("Using cached data...")
            response = cache_data[url]
        else:
            response = make_request(url)
            cache_data[url] = response
            save_cache(cache_file, cache_data)

        search(response)

    elif sys.argv[1] == "-s" and len(sys.argv) <= 3:
        if len(sys.argv) != 3:
            print("Usage: go2web -s <search-term>")
            sys.exit(1)
        search_term = sys.argv[2]
        search_term = search_term.replace(" ", "+")
        cache_data = load_cache(cache_file)

        if cache_data.get(search_term):
            print("Using cached data...")
            results = cache_data[search_term]
        else:
            results = make_request(f"https://www.bing.com/search?q={search_term}")
            cache_data[search_term] = results
            save_cache(cache_file, cache_data)

        print_search(results)

    elif sys.argv[1] == "-u" and sys.argv[3] == "-s":
        url = sys.argv[2]
        search_term = sys.argv[4]
        search_term = search_term.replace(" ", "+")
        results = make_request((f"{url}/search?q={search_term}"))
        search(results)

    else:
        print("Invalid option. Use -h for help."


if __name__ == "__main__":
    main()
