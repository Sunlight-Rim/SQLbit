# def binary_search(query, x, xmin):
#     xmax = x
#     while True:
#         if query < x:
#             xmax = min(xmax, x)
#         else:
#             if xmax - xmin == 1:
#                 print('answ is', xmin)
#                 return xmin
#             xmin = max(xmin, x)
#         print(x)
#         x = xmin + (xmax - xmin) // 2
#
# binary_search(1500, 100000, 1)

import asyncio
import aiohttp

async def async_parse_with_query(url, cookies):
    # try:
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url) as resp:
            html = await resp.text()
    #         soup = BeautifulSoup(html, "lxml")
    # if soup.findAll(string=res_expected):
    #     cell_bin[pow_2] = 1
    # else:
    #     cell_bin[pow_2] = 0
    return

def main():
    ioloop = asyncio.get_event_loop()
    tasks = []
    for i in range(3):
        tasks.append(ioloop.create_task(async_parse_with_query("https://yahoo.com/", {"1":str(i)})))
    wait_tasks = asyncio.wait(tasks)
    ioloop.run_until_complete(wait_tasks)
    ioloop.close()


main()
