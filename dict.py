import requests
import threading
from bs4 import BeautifulSoup
import sqlite3
import sys
import datetime
import traceback

# ANSI颜色代码
BLUE = '\x1b[94m'
RED = '\033[31m'
YELLOW = '\033[33m'
GREEN = '\033[32m'
RESET = '\033[0m'
CLEAR_SCREEN = '\033[H\033[J'

def getch():
    """轻量级读取单个字符输入，不显示在命令行上"""
    if sys.platform == 'win32':
        import msvcrt
        return msvcrt.getch().decode()
    else:
        return sys.stdin.read(1).decode()


def show_word(word_info):
    index = 0 
    word = word_info['word']
    pronounce = word_info['pronounce']
    def_num = len(word_info['definitions'])
    while index < def_num: 
        sense_block = word_info['definitions'][index]
        part_of_speech = sense_block['part_of_speech']

        output = f'''{word}
{GREEN}{pronounce}{RESET}
{BLUE}<{part_of_speech}>{RESET}
{RED}{sense_block['english_def']}{RESET}
{YELLOW}{sense_block['chinese_translation']}{RESET}
'''
        
        for example in sense_block['examples']:
            output += f'''{RED}- {example['sentence']}{RESET}
{YELLOW}  {example['translation']}{RESET}
'''

        output += f'[{index + 1}/{def_num}]'
        print(output)
        
        # 读取单个字符输入
        while True:
            input_char = getch()
            if input_char.isdigit():
                index = int(input_char)
                continue
            elif input_char.lower() == 'h':
                if index > 0:
                    index -= 1
                    break
            elif input_char.lower() == 'l':
                if index < def_num - 1:
                    index += 1
                    break
            elif input_char.lower() == 'n':
                print(CLEAR_SCREEN, end='')
                return
            elif input_char.lower() == 'q':
                exit(0)
                
        print(CLEAR_SCREEN, end='')

def get_word_meaning(word):
    url = 'http://localhost:2006/search'
    params = {'word': word}
    # 发送 GET 请求
    response = requests.get(url, params=params)
    response.raise_for_status()  # 如果响应状态码不是 200，将引发 HTTPError 异常
    return response.json()


if __name__ == "__main__":
    print(CLEAR_SCREEN, end='')
    while True:
        try:
            # 命令行输入
            word = input("Query: ").lower()

            # 忽略空白字符和字母
            if (len(word) <= 1):

                # 输入 q 则退出程序
                if (word.lower() == 'q'):
                    break

                continue
        
            print(CLEAR_SCREEN, end='')
            word_info = get_word_meaning(word)
            show_word(word_info)
        except Exception as e:
            traceback.print_exc()
            print(e)
            print("something wrong T^T")