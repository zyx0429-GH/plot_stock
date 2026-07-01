import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

matches = list(re.finditer(r'const scatterData = ', content))
print('scatterData occurrences:', len(matches))

if matches:
    start = matches[0].end()
    bracket_count = 0
    in_string = False
    string_char = None
    end_pos = start
    for i, c in enumerate(content[start:]):
        if in_string:
            if c == string_char and content[start+i-1] != '\\':
                in_string = False
        else:
            if c in '"\'':
                in_string = True
                string_char = c
            elif c == '[':
                bracket_count += 1
            elif c == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_pos = start + i + 1
                    break
    
    data_str = content[start:end_pos]
    stock_count = data_str.count('"stock_id"')
    print('Stock count in scatterData:', stock_count)
    print('Data string length:', len(data_str))
