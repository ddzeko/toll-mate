#!/bin/bash
curl -sS -X POST http://127.0.0.1:5000/api/routeInfo \
  -H "Content-Type: application/json" \
  -d '{"hac_ulaz": "Karlovac", "hac_izlaz": "Vučevica"}' \
  -D response.head \
  -o response.body
