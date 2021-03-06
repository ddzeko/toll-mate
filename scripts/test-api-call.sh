#!/bin/bash

testUri=/api/routeInfo

if [[ -z "$PYTHONANYWHERE_DOMAIN" ]]; then
    testSite="http://127.0.0.1:5000"
else
    if [[ -z "$WSGI_MODULE" ]]; then
        testSite="${LOGNAME}.${PYTHONANYWHERE_DOMAIN}"
    else
        testSite=${WSGI_MODULE%%_wsgi}
        testSite=${testSite//_/.}
    fi
    testSite="https://${testSite}"
fi

rm -f response.head response.body 2>&- >&-
curl -sS -X POST "${testSite}${testUri}" \
  -H "Content-Type: application/json" \
  -d '{ "hac_ulaz": "Karlovac", "hac_izlaz": "Vučevica" }' \
  -D response.head \
  -o response.body
