import sys
import re
import os.path
import secrets
import uuid

def replace_referents(data):
    cache = {}
    def _replace_ref(match):
        ref = match.group(1)
        if not ref in cache:
            cache[ref] = ("RBX" + secrets.token_hex(16).upper()).encode()
        return cache[ref]
    data = re.sub(
        b"(RBX[A-Z0-9]{32})",
        _replace_ref,
        data
    )
    return data

def replace_script_guids(data):
    cache = {}
    def _replace_guid(match):
        guid = match.group(1)
        if not guid in cache:
            cache[guid] = ("{" + str(uuid.uuid4()).upper() + "}").encode()
        return cache[guid]
    data = re.sub(
        b"(\{[A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12}\})",
        _replace_guid,
        data
    )
    return data

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fpath = sys.argv[1]
    else:
        fpath = input("filename: ").strip()
    
    if not os.path.isfile(fpath):
        exit(f"'{fpath}' does not exist")
    if not fpath.endswith(".rbxlx"):
        exit("must be a .rbxlx file")
    
    with open(fpath, "rb") as fp:
        data = fp.read()

    data = replace_referents(data)
    data = replace_script_guids(data)

    new_fpath = os.path.join(
        os.path.dirname(fpath),
        os.path.splitext(os.path.basename(fpath))[0] + "_clean" \
            + os.path.splitext(os.path.basename(fpath))[1]
    )

    with open(new_fpath, "wb") as fp:
        fp.write(data)
    
    exit(f"saved clean file to {new_fpath}")