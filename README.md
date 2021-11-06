# Just another Blind SQL Injection Tool
A script for automatize boolean-based blind SQL injections. \
Uses [binary search](https://en.wikipedia.org/wiki/Binary_search_algorithm).
Works with SQLite at least, supports using cookies.

On the current moment it can:
* Search row values by columns in a table
* Search characters count in a row by column in a table
* Search rows count in a table

Optimization idea:
Use multithreading with bitwise comparison.
![idea](idea.jpg)
## Intsall
```
git clone https://github.com/Sunlight-Rim/just_another_blind_injection_tool.git
cd just_another_blind_injection_tool
python main.py
```
Specify the data in the config file or in the program input.

![screenshot](screenshot.png)
