```$env:DB_HOST="localhost";``` 
```$env:DB_HOST="185.4.75.245";``` 
```$env:DB_HOST="localhost"; uvicorn app.backend.main:app```
```$env:DB_HOST="localhost"; alembic revision --autogenerate -m "database_creation"```
```alembic upgrade head```

DEV: ```docker run -d --name my-postgres -e POSTGRES_USER=vlad -e POSTGRES_PASSWORD=odfjpskofnpknvkrsngljapokn -e POSTGRES_DB=mining -p 5432:5432 postgres:latest```
DEV: ```docker exec -it DEV_POSTGRES psql "host=localhost port=5432 dbname=mining user=vlad password='odfjpskofnpknvkrsngljapokn'"```

```pytest .\tests -s -v```
ACTUAL: ```pytest --cov=app --cov-report=html:ztest tests -v```


```docker build -f Dockerfile-back -t back-image .```
```docker run --name back-container -d back-image```


