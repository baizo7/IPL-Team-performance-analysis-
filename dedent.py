import codecs
with codecs.open('api/charts_legacy.py', 'r', 'utf-8') as f:
    lines = f.readlines()
new_lines = []
for line in lines:
    if line.startswith('    '):
        new_lines.append(line[4:])
    else:
        new_lines.append(line)
with codecs.open('api/charts_legacy.py', 'w', 'utf-8') as f:
    f.writelines(new_lines)
