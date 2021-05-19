#!/usr/bin/env python3

import os

import backoff
import requests
import numpy as np
from datetime import timedelta, date, datetime

import singer
from singer import Transformer, utils

LOGGER = singer.get_logger()
SESSION = requests.Session()

BASE_API_URL = "https://deutsche-feiertage-api.de/api/v1/"
CONFIG = {}
STATE = {}

def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schema(entity):
    return utils.load_json(get_abs_path("schemas/{}.json".format(entity)))


def load_and_write_schema(name, key_properties="id", bookmark_property="updated_at"):
    schema = load_schema(name)
    singer.write_schema(name, schema, key_properties, bookmark_properties=[bookmark_property])
    return schema

def get_url():
    return BASE_API_URL


@backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_tries=5,
    giveup=lambda e: e.response is not None and 400 <= e.response.status_code < 500,
    factor=2)
@utils.ratelimit(100, 15)
def request(url, year):
    headers = {"X-DFA-Token": "dfa"}
    req = requests.Request("POST", url=url+str(year), headers=headers).prepare()
    LOGGER.info("POST {}".format(req.url))
    resp = SESSION.send(req)
    resp.raise_for_status()
    return resp.json()

# Any date-times values can either be a string or a null.
# If null, parsing the date results in an error.
# Instead, removing the attribute before parsing ignores this error.
def remove_empty_date_times(item, schema):
    fields = []

    for key in schema["properties"]:
        subschema = schema["properties"][key]
        if subschema.get("format") == "date-time":
            fields.append(key)

    for field in fields:
        if item.get(field) is None:
            del item[field]

def sync_endpoint(schema_name, year):
    schema = load_schema(schema_name)

    singer.write_schema(schema_name,
                        schema,
                        ["id"])

    with Transformer() as transformer:

        url = get_url()

        response = request(url, year)

        time_extracted = utils.now()

        for row in response["holidays"]:

            LOGGER.info(row)

            aligned_row = {"date": row["date"], "name": row["name"]}

            item = transformer.transform(aligned_row, schema)

            singer.write_record(schema_name,
                                item,
                                time_extracted=time_extracted)

    singer.write_state(STATE)


def do_sync():
    LOGGER.info("Starting sync")

    today = datetime.now()
    years = range(2010,today.year)

    for year in years:
        sync_endpoint("holidays", year)
    
    LOGGER.info("Sync complete")

def main_impl():
    do_sync()

def main():
    try:
        main_impl()
    except Exception as exc:
        LOGGER.critical(exc)
        raise exc


if __name__ == "__main__":
    main()
