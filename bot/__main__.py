import logging
from bot import app

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] === [%(levelname)s] === %(message)s")

app.run()