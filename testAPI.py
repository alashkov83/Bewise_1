#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests as r

BASE_URL = "http://127.0.0.1:8080"

resp = r.post(BASE_URL, json={"questions_num": 20})
print(resp.status_code)
print(resp.json())

