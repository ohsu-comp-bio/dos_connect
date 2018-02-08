
# dos_connect server

The dos connect server has a pluggable model for:
* authentication
* backend persistence

This readme guides you through the setup and example use cases.
We use s3_inventory for these examples, other apps work the same.

## setup
```
export  $(cat .env | grep -v "#" | xargs )
```

## default

* http
* no auth
* memory backend

### server
```
$ python -m dos_connect.server.app
using authorizer dos_connect.server.noop_authorizer to change set AUTHORIZER envvar
using backend dos_connect.server.memory_backend to change set BACKEND envvar
 * Running on http://0.0.0.0:8080/ (Press CTRL+C to quit)
```

### client
```
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID  \
 AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
 AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
 python -m dos_connect.apps.inventory.s3_inventory \
   --dos_server http://localhost \
   $AWS_TEST_BUCKET
```

## auth (api key)

* https
* keystone (openstack) api token auth
* memory backend

### server
```
# source openstack's rc file first
sudo \
  OS_AUTH_URL=http://xxxxx:pppp/v3 \
  AUTHORIZER=dos_connect.server.keystone_api_key_authorizer \
  python -m dos_connect.server.app \
    -K $(pwd)/certs/certificate.key \
    -C $(pwd)/certs/certificate.pem  \
    -P 443
```

### client
```
# where DOS_API_KEY is from openstack's `openstack token issue`
DOS_API_KEY=XXXX \
 AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID  \
 AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
 AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
 python -m dos_connect.apps.inventory.s3_inventory \
   --dos_server https://localhost \
   $AWS_TEST_BUCKET
```


## auth (basic auth)

* https
* basic auth
* memory backend

### server
```
# user.htpasswd needs to exist in default dir
sudo \  
  AUTHORIZER=dos_connect.server.basic_authorizer \
  python -dos_connect.server.app \
    -K $(pwd)/certs/certificate.key \
    -C $(pwd)/certs/certificate.pem  \
    -P 443
```

### client
```
# note: if using self signed certs you may need to update `certifi`
# CA file with your host's certificate
# https://github.com/certifi/python-certifi/blob/master/certifi/cacert.pem
 DOS_USER_PASSWD=bob:password \
 AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID  \
 AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
 AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
 python -m dos_connect.apps.inventory.s3_inventory \
   --dos_server https://localhost \
   $AWS_TEST_BUCKET
```


## elastic backend

* https
* no auth
* elastic search backend

### server
```
# defaults to localhost:9200, set ELASTIC_URL=<url> to override
sudo \  
  BACKEND=dos_connect.server.elasticsearch_backend  ES_REFRESH_ON_PERSIST=true \
  python -m dos_connect.server.app \
    -K $(pwd)/certs/certificate.key \
    -C $(pwd)/certs/certificate.pem  \
    -P 443
```

### client
```
#
 AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID  \
 AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
 AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
 python -m dos_connect.apps.inventory.s3_inventory \
   --dos_server https://localhost \
   $AWS_TEST_BUCKET
```
