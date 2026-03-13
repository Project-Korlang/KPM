#!/usr/bin/env python3
import argparse
import json
import os
import sys
import hashlib
import requests
import datetime
import re
import subprocess
from collections import Counter
from urllib.parse import urlparse

# Try importing dependencies, handle missing ones gracefully
try:
    import jsonschema
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    print("Missing dependencies. Please run: pip install -r requirements.txt")
    sys.exit(1)

REGISTRY_ROOT = os.path.dirname(os.path.abspath(__file__))
PACKAGES_DIR = os.path.join(REGISTRY_ROOT, 'packages')
AUTHORS_DIR = os.path.join(REGISTRY_ROOT, 'authors')
SCHEMAS_DIR = os.path.join(REGISTRY_ROOT, 'schemas')
INDEX_FILE = os.path.join(REGISTRY_ROOT, 'index.json')
PACKAGE_SCHEMA_FILE = os.path.join(SCHEMAS_DIR, 'package.schema.json')
AUTHOR_SCHEMA_FILE = os.path.join(SCHEMAS_DIR, 'author.schema.json')

def load_schema(schema_path):
    with open(schema_path, 'r') as f:
        return json.load(f)

def log_success(msg):
    print(f"{Fore.GREEN}✓ {msg}")

def log_error(msg):
    print(f"{Fore.RED}✗ {msg}")

def log_warn(msg):
    print(f"{Fore.YELLOW}⚠ {msg}")

def log_info(msg):
    print(f"{Fore.CYAN}ℹ {msg}")

def validate_manifest(manifest_path, schema):
    try:
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        jsonschema.validate(instance=data, schema=schema)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON Error: {str(e)}"
    except jsonschema.ValidationError as e:
        return None, f"Schema Error: {e.message}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def cmd_validate(args):
    schema = load_schema(PACKAGE_SCHEMA_FILE)
    errors = 0
    package_files = [f for f in os.listdir(PACKAGES_DIR) if f.endswith('.json')]
    
    print(f"Validating {len(package_files)} packages...")
    
    for filename in package_files:
        path = os.path.join(PACKAGES_DIR, filename)
        data, error = validate_manifest(path, schema)
        if error:
            log_error(f"{filename}: {error}")
            errors += 1
        else:
            # Check filename matches package name
            if f"{data['name']}.json" != filename:
                 log_error(f"{filename}: Filename must match package name '{data['name']}'")
                 errors += 1
            else:
                 pass # Silent success for brevity, or use -v flag

    if errors == 0:
        log_success("All packages validated successfully.")
    else:
        log_error(f"Found {errors} errors.")
        sys.exit(1)

def cmd_index(args):
    packages = []
    files = [f for f in os.listdir(PACKAGES_DIR) if f.endswith('.json')]
    
    for filename in files:
        with open(os.path.join(PACKAGES_DIR, filename), 'r') as f:
            try:
                data = json.load(f)
                # Minimal index entry
                entry = {
                    "name": data['name'],
                    "version": data['version'],
                    "description": data['description'],
                    "keywords": data.get('keywords', []),
                    "authors": data['authors'],
                    "updated_at": data['published_at'],
                    "deprecated": data.get('deprecated', False)
                }
                packages.append(entry)
            except Exception as e:
                log_error(f"Skipping {filename}: {e}")

    # Sort by update time desc
    packages.sort(key=lambda x: x['updated_at'], reverse=True)
    
    index_data = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "package_count": len(packages),
        "packages": packages
    }
    
    with open(INDEX_FILE, 'w') as f:
        json.dump(index_data, f, separators=(',', ':')) # Minified
    
    log_success(f"Generated index.json with {len(packages)} packages.")

def cmd_stats(args):
    if not os.path.exists(INDEX_FILE):
        log_error("Index file not found. Run 'manage.py index' first.")
        return

    with open(INDEX_FILE, 'r') as f:
        index = json.load(f)
    
    packages = index['packages']
    total_pkgs = len(packages)
    
    # Author stats
    all_authors = []
    keywords = []
    for p in packages:
        all_authors.extend(p.get('authors', []))
        keywords.extend(p.get('keywords', []))
    
    unique_authors = set(all_authors)
    top_keywords = Counter(keywords).most_common(5)
    
    print(f"\n{Style.BRIGHT}Registry Statistics:{Style.RESET_ALL}")
    print(f"Total Packages: {Fore.YELLOW}{total_pkgs}")
    print(f"Total Authors:  {Fore.YELLOW}{len(unique_authors)}")
    print(f"Most Recent:    {Fore.CYAN}{packages[0]['name']} ({packages[0]['version']})")
    
    print(f"\n{Style.BRIGHT}Top Keywords:{Style.RESET_ALL}")
    for k, c in top_keywords:
        print(f"  {k}: {c}")
    print("")

def verify_checksum(url, expected_sha256):
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        sha256 = hashlib.sha256()
        for chunk in response.iter_content(chunk_size=8192):
            sha256.update(chunk)
            
        calculated = sha256.hexdigest()
        if calculated == expected_sha256:
            return True, "Match"
        else:
            return False, f"Mismatch: expected {expected_sha256}, got {calculated}"
    except Exception as e:
        return False, f"Download error: {str(e)}"

def verify_gpg_signature(file_path, signature_str, public_key_str):
    """Verifies a GPG signature using a public key string."""
    try:
        # Create temporary file for signature and public key
        with open("temp.sig", "w") as f:
            f.write(signature_str)
        with open("temp.pub", "w") as f:
            f.write(public_key_str)
            
        # Import public key
        subprocess.run(["gpg", "--import", "temp.pub"], capture_output=True)
        
        # Verify
        result = subprocess.run(["gpg", "--verify", "temp.sig", file_path], capture_output=True, text=True)
        
        os.remove("temp.sig")
        os.remove("temp.pub")
        
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)

def cmd_verify(args):
    name = args.name
    path = os.path.join(PACKAGES_DIR, f"{name}.json")
    
    if not os.path.exists(path):
        log_error(f"Package '{name}' not found.")
        return
    
    with open(path, 'r') as f:
        data = json.load(f)
        
    url = data['download_url']
    expected = data['checksum']['sha256']
    
    log_info(f"Verifying {name}@{data['version']}...")
    log_info(f"URL: {url}")
    
    # Download tarball for verification
    temp_file = "temp_package.tar.gz"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(temp_file, "wb") as f:
            f.write(response.content)
    except Exception as e:
        log_error(f"Failed to download package: {e}")
        sys.exit(1)

    # Checksum
    sha256 = hashlib.sha256(open(temp_file, 'rb').read()).hexdigest()
    if sha256 == expected:
        log_success("Checksum matched.")
    else:
        log_error(f"Checksum mismatch: expected {expected}, got {sha256}")
        os.remove(temp_file)
        sys.exit(1)

    # Signature
    if 'signature' in data['checksum']:
        signature = data['checksum']['signature']
        # Try to find author's public key
        author_handle = data['authors'][0]
        author_path = os.path.join(AUTHORS_DIR, f"{author_handle}.json")
        if os.path.exists(author_path):
            with open(author_path, 'r') as af:
                author_data = json.load(af)
                public_key = author_data.get('public_key')
                if public_key:
                    log_info(f"Verifying signature for author '{author_handle}'...")
                    success, msg = verify_gpg_signature(temp_file, signature, public_key)
                    if success:
                        log_success("GPG Signature verified.")
                    else:
                        log_warn(f"GPG Signature verification failed: {msg}")
                else:
                    log_info("Author has no public key listed. Skipping signature check.")
        else:
            log_info(f"Author profile '{author_handle}' not found. Skipping signature check.")
    
    os.remove(temp_file)

def cmd_sign(args):
    """Helper for authors to sign their package tarball."""
    file_path = args.file
    if not os.path.exists(file_path):
        log_error(f"File {file_path} not found.")
        return
        
    log_info(f"Signing {file_path} with default GPG key...")
    try:
        # Generate detached armor signature
        result = subprocess.run(["gpg", "--detach-sign", "--armor", "--output", "-", file_path], 
                                capture_output=True, text=True, check=True)
        print("\n--- BEGIN GPG SIGNATURE ---")
        print(result.stdout)
        print("--- END GPG SIGNATURE ---\n")
        log_success("Signature generated. Copy the content above into your manifest's 'checksum.signature' field.")
    except Exception as e:
        log_error(f"GPG signing failed: {e}")

def cmd_search(args):
    query = args.query.lower()
    if not os.path.exists(INDEX_FILE):
        log_warn("Index not found. Searching raw package files...")
        files = [f for f in os.listdir(PACKAGES_DIR) if f.endswith('.json')]
        results = []
        for f in files:
            with open(os.path.join(PACKAGES_DIR, f), 'r') as pf:
                data = json.load(pf)
                if query in data['name'].lower() or query in data['description'].lower():
                    results.append(data)
    else:
        with open(INDEX_FILE, 'r') as f:
            index = json.load(f)
        results = [p for p in index['packages'] if query in p['name'].lower() or query in p['description'].lower()]

    if not results:
        log_info("No packages found.")
        return

    print(f"\nFound {len(results)} packages:")
    for p in results:
        print(f"{Fore.GREEN}{p['name']:<20} {Fore.CYAN}{p['version']:<10} {Style.DIM}{p['description']}")

def cmd_add(args):
    source = args.manifest_file
    if not os.path.exists(source):
        log_error(f"File {source} not found.")
        sys.exit(1)
        
    schema = load_schema(PACKAGE_SCHEMA_FILE)
    data, error = validate_manifest(source, schema)
    
    if error:
        log_error(f"Validation failed: {error}")
        sys.exit(1)
        
    dest_name = f"{data['name']}.json"
    dest_path = os.path.join(PACKAGES_DIR, dest_name)
    
    if os.path.exists(dest_path):
        log_warn(f"Overwriting existing package {data['name']}.")
    
    with open(dest_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    log_success(f"Added {dest_name} to packages/.")
    cmd_index(None)

def cmd_deprecate(args):
    name = args.name
    path = os.path.join(PACKAGES_DIR, f"{name}.json")
    
    if not os.path.exists(path):
        log_error(f"Package '{name}' not found.")
        return
        
    with open(path, 'r') as f:
        data = json.load(f)
        
    if data.get('deprecated'):
        log_warn(f"{name} is already deprecated.")
        return
        
    data['deprecated'] = True
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        
    log_success(f"Marked {name} as deprecated.")
    cmd_index(None)

def cmd_lint(args):
    errors = 0
    files = [f for f in os.listdir(PACKAGES_DIR) if f.endswith('.json')]
    
    # 1. Check for duplicates (case insensitive)
    names = [f[:-5] for f in files]
    lower_names = [n.lower() for n in names]
    if len(names) != len(set(lower_names)):
        log_error("Duplicate package names found (case-insensitive clash).")
        errors += 1
        
    for filename in files:
        path = os.path.join(PACKAGES_DIR, filename)
        with open(path, 'r') as f:
            try:
                data = json.load(f)
            except:
                continue
                
        # 2. Namespace check
        # A package named "johndoe/utils" must have "johndoe" as an author
        pkg_name = data['name']
        if '/' in pkg_name:
            namespace = pkg_name.split('/')[0]
            if namespace not in data['authors']:
                log_error(f"{pkg_name}: Namespace '{namespace}' must be listed in authors.")
                errors += 1
                
            # Check if author exists in authors/
            author_file = os.path.join(AUTHORS_DIR, f"{namespace}.json")
            if not os.path.exists(author_file):
                 log_error(f"{pkg_name}: Namespace author '{namespace}' does not exist in authors/.")
                 errors += 1
            else:
                 # Check if author is verified (implied requirement)
                 with open(author_file, 'r') as af:
                     author_data = json.load(af)
                     if not author_data.get('verified', False):
                         log_warn(f"{pkg_name}: Namespace author '{namespace}' is not verified.")

        # 3. Check suspicious URLs
        url = data.get('download_url', '')
        if not (url.startswith('https://github.com') or url.startswith('https://gitlab.com') or url.startswith('https://api.github.com')):
            log_warn(f"{pkg_name}: Non-standard download URL host: {url}")
            
    if errors == 0:
        log_success("Linting passed.")
    else:
        log_error(f"Linting failed with {errors} errors.")
        sys.exit(1)

def cmd_generate_author(args):
    handle = args.handle
    path = os.path.join(AUTHORS_DIR, f"{handle}.json")
    
    if os.path.exists(path):
        log_error(f"Author {handle} already exists.")
        sys.exit(1)
        
    data = {
        "handle": handle,
        "name": "Display Name",
        "email_hash": "00000000000000000000000000000000",
        "verified": False,
        "packages": [],
        "joined_at": datetime.datetime.utcnow().isoformat() + "Z",
        "github_url": f"https://github.com/{handle}"
    }
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        
    log_success(f"Created author template at authors/{handle}.json")

def main():
    parser = argparse.ArgumentParser(description="KPM Registry Manager")
    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')
    
    subparsers.add_parser('validate', help='Validate all packages')
    subparsers.add_parser('index', help='Regenerate index.json')
    subparsers.add_parser('stats', help='Show registry stats')
    subparsers.add_parser('lint', help='Lint registry consistency')
    
    verify_p = subparsers.add_parser('verify', help='Verify package checksum and signature')
    verify_p.add_argument('name', help='Package name')
    
    sign_p = subparsers.add_parser('sign', help='Sign a package tarball')
    sign_p.add_argument('file', help='Path to tarball')

    search_p = subparsers.add_parser('search', help='Search for packages')
    search_p.add_argument('query', help='Search query')

    add_p = subparsers.add_parser('add', help='Add a package')
    add_p.add_argument('manifest_file', help='Path to new manifest.json')
    
    deprecate_p = subparsers.add_parser('deprecate', help='Deprecate a package')
    deprecate_p.add_argument('name', help='Package name')
    
    gen_auth_p = subparsers.add_parser('generate-author', help='Scaffold new author')
    gen_auth_p.add_argument('handle', handle='Author handle')

    args = parser.parse_args()
    
    if args.command == 'validate':
        cmd_validate(args)
    elif args.command == 'index':
        cmd_index(args)
    elif args.command == 'stats':
        cmd_stats(args)
    elif args.command == 'verify':
        cmd_verify(args)
    elif args.command == 'sign':
        cmd_sign(args)
    elif args.command == 'search':
        cmd_search(args)
    elif args.command == 'add':
        cmd_add(args)
    elif args.command == 'deprecate':
        cmd_deprecate(args)
    elif args.command == 'lint':
        cmd_lint(args)
    elif args.command == 'generate-author':
        cmd_generate_author(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
