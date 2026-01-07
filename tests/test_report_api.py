import requests

# Test the report endpoint
url = 'http://localhost:8000/api/v1/projects/c547af27-0443-4356-9541-49721a440575/report?format=pdf'
print(f'Testing endpoint: {url}')
try:
    response = requests.get(url, timeout=10)
    print(f'Status: {response.status_code}')
    print(f'Content-Type: {response.headers.get("content-type")}')
    if response.status_code == 200:
        print(f'Response size: {len(response.content)} bytes')
    else:
        print(f'Error: {response.text[:200]}')
except Exception as e:
    print(f'Exception: {str(e)}')
