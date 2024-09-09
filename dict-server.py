
import requests
import threading
from bs4 import BeautifulSoup
import sqlite3
import sys
import datetime
import socket
from flask import Flask, request, jsonify


conn = sqlite3.connect('word_database.db', check_same_thread=False)
cursor = conn.cursor()

def insert_revise(word_id):
    cursor.execute('select * from revise where word_id = ?', (word_id,))
    result = cursor.fetchone()
    time_str = datetime.datetime.now().strftime('%Y-%m-%d')
    if result is None:
        cursor.execute("INSERT INTO revise (word_id, time, next_time) VALUES (?, ?, ?)", (word_id, time_str, 1))
        conn.commit()
    else:
        cursor.execute("UPDATE revise SET time =?, next_time =? WHERE word_id =?", (time_str, 1, word_id))


def insert_example(meaning_id, example):
    cursor.execute("INSERT INTO examples (meaning_id, sentence, sentence_ch) VALUES (?,?,?)", (meaning_id, example['sentence'], example['translation']))


def insert_meaning(id, definition):
    cursor.execute("INSERT INTO meanings (word_id, pos, meaning, meaning_ch) VALUES (?,?,?, ?)", (id, definition['part_of_speech'], definition['english_def'], definition['chinese_translation']))
    id = cursor.lastrowid
    for example in definition['examples']:
        insert_example(id, example)


def insert_word(word):
    # 检查单词是否已经在数据库中
    cursor.execute('SELECT * FROM words WHERE word = ?', (word['word'],))

    # 单词不在数据库中，添加新单词
    result = cursor.fetchone()
    if result is None:
        pronounce = word['pronounce']
        cursor.execute("INSERT INTO words (word, pronounce) VALUES (?, ?)", (word['word'], pronounce))
        id = cursor.lastrowid
        for meaning in word['definitions']:
            insert_meaning(id, meaning)
        insert_revise(id)
        conn.commit()
    else:
        id = result[0]
        insert_revise(id)
        conn.commit()


def getch():
    """轻量级读取单个字符输入，不显示在命令行上"""
    if sys.platform == 'win32':
        import msvcrt
        return msvcrt.getch().decode()
    else:
        return sys.stdin.read(1).decode()


def request_word_page(word):
    # 剑桥词典单词释义页面的URL模板
    url = f"https://dictionary.cambridge.org/dictionary/english-chinese-simplified/{word}"

    # 定义请求头，模拟浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    # 尝试发送请求，并处理可能的连接错误
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 如果响应状态码不是200，将抛出HTTPError异常
    except requests.HTTPError as e:
        return None
    
    # 使用Beautiful
    return BeautifulSoup(response.text, 'html.parser')


def get_word_meaning(word):
    soup = request_word_page(word)

    if soup is None:
        print("HTTP错误")

    # 初始化一个字典来存储信息
    word_info = {
        'word': None,
        'definitions': [] 
    }

    # 提取单词
    # 初始化一个字典来存储信息
    word_info = {
        'word': None,
        'uk_pron': None,
        'us_pron': None,
        'definitions': [] 
    }


    # 提取单词
    headword = soup.find('span', class_='headword')
    if headword is None:
        word_info['word'] = headword.text
    else:
        word_info['word'] = word

    # 提取发音
    pos_elements = soup.find_all('div', class_='entry-body__el')
    prons = soup.find_all('span', class_=['pron', 'dpron'])
    uk_pron = prons[0].text
    us_pron = prons[1].text
    pronounce = f'UK {uk_pron} US {us_pron}'
    word_info['pronounce'] = pronounce

    # 查找所有的词性（pos）及其释义块（ddef_block）
    for pos_element in pos_elements:
        part_of_speech = pos_element.find('span', class_='dpos').text

        # 提取当前词性下的所有释义块（ddef_block）
        for ddef_block in pos_element.find_all('div', class_='ddef_block'):
            sense = {
                'part_of_speech': part_of_speech,
                'english_def': None,
                'chinese_translation': None,
                'examples': []
            }

            # 提取英文释义
            english_def = ddef_block.find('div', class_='def')
            if english_def is not None:
                english_def = english_def.text.strip()
            else:
                print(f"{RED} English Definition Is None {RESET}")
                return
            
            # 提取中文翻译
            chinese_translation = ddef_block.find('span', class_=['trans', 'dtrans'])
            if chinese_translation is not None:
                chinese_translation = chinese_translation.text.strip()
            
            # 添加释义到当前词性的定义列表
            sense['english_def'] = english_def
            sense['chinese_translation'] = chinese_translation
            
            # 提取并添加例句及其翻译
            examples = ddef_block.find_all('div', class_='examp')
            sense['examples'] = []
            for ex in examples:
                sentence = ex.find('span', class_=['eg', 'deg'])
                if sentence is not None:
                    sentence = sentence.text.strip()
                
                translation = ex.find('span', class_=['trans', 'dtrans'])
                if translation is not None:
                    translation = translation.text.strip()
                example = {
                    'sentence': sentence,
                    'translation': translation 
                }
                sense['examples'].append(example)

            # 将当前词性的信息添加到单词信息中
            word_info['definitions'].append(sense)
    
    return word_info

app = Flask(__name__)

@app.route('/search', methods=['GET'])
def search():
    # 从请求中获取单词
    word = request.args.get('word', default='', type=str)
    # 调用函数处理请求
    word_info = get_word_meaning(word)
    insert_word(word_info)
    # 返回结果
    return jsonify(word_info)

if __name__ == '__main__':
    app.run(port=2006)

# 
# if __name__ == "__main__":
#     print(CLEAR_SCREEN, end='')
#     while True:
#         try:
#             word = 
#             word_info = get_word_meaning(word)
#             show_word(word_info)
#         except Exception as e:
#             print(e)
#             print("something wrong T^T")