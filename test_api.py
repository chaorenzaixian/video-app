#!/usr/bin/env python3
import requests
r = requests.post('http://localhost:8000/api/v1/auth/guest/register', json={'device_id':'test1234567890'})
print(r.status_code, r.text)
