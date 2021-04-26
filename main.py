import json
import random
import time
from datetime import datetime, timezone, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config.builder import Builder
from config.config import config
from logs import logger
from presentation.observer import Observable

import threading
import requests
from tinydb import TinyDB , Query

DATA_SLICE_DAYS = 1
DATETIME_FORMAT = "%Y-%m-%dT%H:%M"

if not os.path.exists("current.json"):
    open("current.json", 'w').close()
xdb = TinyDB("current.json")
db=xdb.table("_default",cache_size=30)

def get_dummy_data():
    logger.info('Generating dummy data')
    random.seed(1)
    return [random.randint(9999, 99000) for _ in range(0, 97)]


def xfetch_prices():
    logger.info('Fetching prices')
    response = requests.get('https://chain.so/api/v2/get_price/DOGE/USD')
    if response.status_code == 200:
        content = response.json()
        prices = content['data']['prices'][0]['price']
        return prices


def main():
    logger.info('Initialize')

    data_sink = Observable()
    builder = Builder(config)
    builder.bind(data_sink)

    try:
        while True:
            try:
                prices = get_dummy_data() if config.dummy_data else fetch_prices()
                data_sink.update_observers(prices)
                time.sleep(config.refresh_interval)
            except (HTTPError, URLError) as e:
                logger.error(str(e))
                time.sleep(5)
    except IOError as e:
        logger.error(str(e))
    except KeyboardInterrupt:
        logger.info('Exit')
        data_sink.close()
        exit()

def fetch_prices():
    item=db.search(Query().type=="dogecoin")
    if len(item) == 0:
        db.insert({type:"dogecoin",prices:[]})
        item=db.search(Query().type=="dogecoin")
    return item[0]["prices"]
class BackgroundTasks(threading.Thread):
    def run(self,*args,**kwargs):
        while True:
            data = xfetch_prices()
            item=db.search(Query().type=="dogecoin")
            if len(item) == 0:
                db.insert({type:"dogecoin",prices:[data]})
            else:
                newlist=list(item[0]["prices"])
                if len(newlist)==24:
                    newlist.pop(0)
                db.update({prices:list(newlist.append(data)},Query().type=="dogecoin")
            time.sleep(60*60)

t = BackgroundTasks()

if __name__ == "__main__":
    t.start()
    main()
