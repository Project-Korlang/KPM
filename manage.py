import json
import os
import sys

INDEX_FILE = 'index.json'

def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r') as f:
            return json.load(f)
    return {"meta": {}, "packages": {}}

def save_index(index):
    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, indent=2)

def register(name, version, url):
    index = load_index()
    if name not in index['packages']:
        index['packages'][name] = {'versions': []}
    
    # Add version if not exists
    versions = index['packages'][name]['versions']
    if not any(v['version'] == version for v in versions):
        versions.append({'version': version, 'url': url})
        print(f'Registered {name}@{version}')
    else:
        print(f'Version {version} already exists for {name}')
    
    save_index(index)

def rollback(name):
    index = load_index()
    if name in index['packages'] and len(index['packages'][name]['versions']) > 1:
        removed = index['packages'][name]['versions'].pop()
        print(f'Rolled back {name}, removed version {removed["version"]}')
        save_index(index)
    else:
        print(f'Cannot rollback {name}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: manage.py register <name> <version> <url> | rollback <name>')
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == 'register':
        register(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == 'rollback':
        rollback(sys.argv[2])
