from typing import Dict, List
import pytest
import subprocess
import time
from app.logger import logger
from models_data.insert_main import main as insert_main_function


@pytest.fixture(scope="session", autouse=True)
def start_postgres_container():
    try:
        subprocess.run(
            ['docker-compose', '-f', 'docker-compose-tests.yml', 'up', '-d', '--build'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)
        subprocess.run(
            ['alembic', 'upgrade', 'head']
        )
        yield
    finally:
        try:
            subprocess.run(
                ['docker-compose', '-f', 'docker-compose-tests.yml', 'down'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            pass


@pytest.fixture(scope="session", autouse=True)
async def fill_db() -> Dict[str, List[Dict]]:
    logger.info("Filling the database...")

    raw_data = await insert_main_function()

    logger.info("Database filled with gpus, coins.")
    
    return raw_data 
