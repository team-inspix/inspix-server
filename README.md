# inspix-server

## caution

this product includes vulnerability

## how to deploy

you can use docker for deplyoing inspix-server. 

```
$ docker build -t inspix .
$ cat .env
INSPIX_DATABASE=database.db
INSPIX_BLUEMIX_USERNAME=hogehoge
INSPIX_BULEMIX_PASSWORD=hogehoge
INSPIX_SECRET=hogehoge
INSPIX_PASSWORD_SALT=hogehoge

$ docker run --env-file .env -p <any port>:5000 inspix
```

## api

view [swagger hub](https://app.swaggerhub.com/api/theoldmoon0602/inspix-server/1.0.0)
