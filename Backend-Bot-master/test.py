import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from app.config import AWS_ACCESS_KEY, AWS_SECRET_KEY

def list_buckets_and_regions():
    try:
        print(AWS_ACCESS_KEY)
        print(AWS_SECRET_KEY)
        s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

        response = s3.list_buckets()
        buckets = response.get('Buckets', [])

        print("Найденные бакеты и их регионы:")
        for bucket in buckets:
            name = bucket['Name']
            location = s3.get_bucket_location(Bucket=name)
            region = location.get('LocationConstraint')
            if region is None:
                region = "us-east-1"
            print(f"- {name}: {region}")

    except NoCredentialsError:
        print("❌ Не найдены AWS ключи. Укажите их через переменные окружения или ~/.aws/credentials")
    except PartialCredentialsError:
        print("❌ Ключи указаны неполностью. Проверьте Access Key и Secret Key.")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    list_buckets_and_regions()
