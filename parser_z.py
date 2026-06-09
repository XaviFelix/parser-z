import csv
import json
import os
import re #regex
import sys


#NOTE: anything after desc will be a collection ie [...]. These get further parsed and properly formatted
# Everything before desc will have one value not a collection
FIELDNAMES = ["line", "model", "sku", "url", "desc", "sockets", "specs", "images"]
ITEM_SEP = "; "
SPEC_SEP = ": "

KEY_WIDTH = max(len(k) for k in ("name", "sku", "url", "desc")) + 1


def parse_js_array(text):
    wrapped = "[" + text.strip() + "]"
    wrapped = re.sub(r'([{,]\s*)([A-Za-z_]\w*)(\s*:)', r'\1"\2"\3', wrapped)
    wrapped = re.sub(r',(\s*[\]}])', r'\1', wrapped)
    return json.loads(wrapped)


def txt_to_csv(txt_file, csv_file):
    with open(txt_file, "r", encoding="utf-8") as f:
        product_lines = parse_js_array(f.read())

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for line in product_lines:
            for model in line["models"]:
                row = {
                    "line": line.get("name", ""),
                    "model": model.get("name", ""),
                    "sku": model.get("sku", ""),
                    "url": model.get("url", ""),
                    "desc": model.get("desc", ""),
                    "sockets": ITEM_SEP.join(model.get("sockets", [])),
                    "specs": ITEM_SEP.join(
                        f"{label}{SPEC_SEP}{value}" for label, value in model.get("specs", [])
                    ),
                    "images": ITEM_SEP.join(model.get("images", [])),
                }
                writer.writerow(row)


def csv_to_txt(csv_file, txt_file):
    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    product_lines = []
    for row in rows:
        if not product_lines or product_lines[-1]["name"] != row["line"]:
            product_lines.append({"name": row["line"], "models": []})
        model = {
            "name": row.get("model", ""),
            "sku": row.get("sku", ""),
            "url": row.get("url", ""),
            "desc": row.get("desc", ""),
            "sockets": [s.strip() for s in row.get("sockets", "").split(ITEM_SEP) if s.strip()],
            "specs": [
                spec.split(SPEC_SEP, 1)
                for spec in row["specs"].split(ITEM_SEP) if spec.strip()
            ],
            "images": [s.strip() for s in row["images"].split(ITEM_SEP) if s.strip()],
        }
        product_lines[-1]["models"].append(model)

    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(format_lines(product_lines))


def kv(key, value):
    return f'{(key + ":").ljust(KEY_WIDTH)} {json.dumps(value)}'


#NOTE: if csv changes, it is reflected here so that it don't break.
def format_lines(product_lines):
    out = []
    for line in product_lines:
        out.append("{\n")
        out.append(f'  name: {json.dumps(line["name"])},\n')
        out.append("  models: [\n")
        for model in line["models"]:
            out.append("    {\n")
            out.append(f'      {kv("name", model["name"])},\n')
            out.append(f'      {kv("sku", model["sku"])},\n')
            out.append(f'      {kv("url", model["url"])},\n')
            out.append(f'      {kv("desc", model["desc"])},\n')

            # anything after desc is a collection of items.
            sockets = ", ".join(json.dumps(s) for s in model.get("sockets", []))
            out.append(f"      sockets: [{sockets}],\n")
            out.append("      specs: [\n")

            for label, value in model["specs"]:
                out.append(f"        [{json.dumps(label)}, {json.dumps(value)}],\n")
            out.append("      ],\n")
            out.append("      images: [\n")

            for image in model["images"]:
                out.append(f"        {json.dumps(image)},\n")
            out.append("      ]\n")
            out.append("    },\n")

        out.append("  ]\n")
        out.append("},\n")
    return "".join(out)

# ------ not part of parsing logic ----------------
#TODO: TUI w/ fzf

def run_file(path):
    base, ext = os.path.splitext(path)
    ext = ext.lower()
    if ext == ".txt":
        csv_file = base + ".csv"
        txt_to_csv(path, csv_file)
        print(f"Done! Converted {path} -> {csv_file}")
    elif ext == ".csv":
        txt_file = base + ".txt"
        csv_to_txt(path, txt_file)
        print(f"Done! Converted {path} -> {txt_file}")
    else:
        raise SystemExit(f"Unsupported file type: {path!r} (expected a .txt or .csv file)")


def show_menu():
    print("=" * 40)
    print("  Zytra Product Parser")
    print("=" * 40)
    print("  1) Convert a .txt or .csv file")
    print("  2) Quit")
    print("-" * 40)

    choice = input("Choose an option [1-2]: ").strip()
    if choice == "1":
        path = input("Enter the path to a .txt or .csv file: ").strip().strip('"')
        run_file(path)
    elif choice == "2":
        print("Goodbye!")
    else:
        print(f"'{choice}' isn't a valid option, please choose 1 or 2.\n")
        show_menu()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        show_menu()