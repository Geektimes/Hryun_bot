from LLM import LLM, requests_limit

def reduction_requests_limit():
    global requests_limit
    requests_limit -= 1
    print(requests_limit)

reduction_requests_limit()