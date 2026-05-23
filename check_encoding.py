import chardet

# Check encoding of generate_html.py
with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\generate_html.py', 'rb') as f:
    raw = f.read(4096)
    result = chardet.detect(raw)
    print('generate_html.py encoding:', result)

# Check encoding of generated index.html
with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\docs\index.html', 'rb') as f:
    raw = f.read(4096)
    result = chardet.detect(raw)
    print('index.html encoding:', result)

# Check the actual bytes around data-threshold
with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\docs\index.html', 'rb') as f:
    content = f.read()
    idx = content.find(b'data-threshold=')
    if idx >= 0:
        snippet = content[idx:idx+50]
        print('Raw bytes around data-threshold:', snippet)
        print('Decoded as utf-8:', snippet.decode('utf-8', errors='replace'))
        print('Decoded as cp950:', snippet.decode('cp950', errors='replace'))
