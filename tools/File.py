

def ReadAllText(url):
    with open(url, 'r+', encoding='utf-8') as fp:
        text = fp.read()
        return text


def WriteAllText(url, text):
    with open(url, 'w+', encoding='utf-8') as fp:
        fp.write(text)
        fp.close()
