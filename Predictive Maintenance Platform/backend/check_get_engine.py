with open('backend/server.py', 'r') as f:
    for line in f:
        if 'get_engine' in line:
            print(line.strip())
