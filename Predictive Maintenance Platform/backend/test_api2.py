
import urllib.request, json
req = urllib.request.Request('http://127.0.0.1:5000/api/analyze', data=b'{\"demo\": true}', headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print('Factors:', data['records'][0]['factors'])
except Exception as e:
    print('Error:', e)

