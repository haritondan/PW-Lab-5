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


def search(search_term):
    try:
        search_url = f"/search?q={search_term}"
        with socket.create_connection(('www.google.md', 80)) as s:
            s.sendall(f"GET {search_url} HTTP/1.1\r\nHost: www.google.md\r\nConnection: close\r\n\r\n".encode())
            response = b''.join(iter(lambda: s.recv(1024), b''))
        soup = BeautifulSoup(response, 'html.parser')
        results = []
        for i, result in enumerate(soup.find_all('a')[16:26], start=1):
            results.append(f"{i}. {result.text} - {result['href']}")
        return '\n'.join(results)
    except Exception as e:
        return f"Error: {e}"


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

        print_url_response(response)

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

        print_search_results(results)

    elif sys.argv[1] == "-u" and sys.argv[3] == "-s":
        url = sys.argv[2]
        search_term = sys.argv[4]
        search_term = search_term.replace(" ", "+")
        results = make_request((f"{url}/search?q={search_term}"))
        print_url_response(results)

    else:
        print("Invalid option. Use -h for help.")


if __name__ == "__main__":
    main()
