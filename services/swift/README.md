# Openstack Swift in Docker
Used for tests.

### Users
| User | Password | Auth key |
| ---- | -------- | -------- |
| admin | admin | admin |
| test | tester | testing |
| test2 | tester2 | testing2 |
| test | tester3 | testing3 |
| user001 | pass001 | apikey |

Stats: `swift -A http://127.0.0.1:8080/auth/v1.0 -U test:tester -K testing stat -v`  
Container list: `swift -A http://127.0.0.1:8080/auth/v1.0 -U test:tester -K testing list`

### Build
`make build`

### Start
`make start`

### Shell into container
`make shell`


### work with swift

 curl -v -H  X-Auth-User:admin:admin -H  X-Auth-Key:admin  http://localhost:8080/auth/v1.0/
 < HTTP/1.1 200 OK
 < X-Storage-Url: http://localhost:8080/v1/AUTH_admin
 < X-Auth-Token: AUTH_tkd9fc673612244508bdfadff6e7e92df6
 < Content-Type: text/html; charset=UTF-8
 < X-Storage-Token: AUTH_tkd9fc673612244508bdfadff6e7e92df6
 < Content-Length: 0
 < X-Trans-Id: txf30dd77f5a494baaae343-0059e8d586
 < Date: Thu, 19 Oct 2017 16:40:38 GMT
 <

 docker exec -it docker-openstack-swift openstack  --os-token AUTH_tkd9fc673612244508bdfadff6e7e92df6 --os-auth-url  http://127.0.0.1:8080/auth/v1.0 --os-url http://localhost:8080/v1/AUTH_admin object create Testing /tmp/ttt
