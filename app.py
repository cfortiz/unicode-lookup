from collections import Counter
from threading import Timer
import argparse
import logging
import unicodedata as ucd

from flask import Flask, request, render_template
import webbrowser


app = Flask(__name__)
logger = logging.getLogger()

ASCII_CONTROL_NAMES = {
    0: "NULL",
    1: "START OF HEADING",
    2: "START OF TEXT",
    3: "END OF TEXT",
    4: "END OF TRANSMISSION",
    5: "ENQUIRY",
    6: "ACKNOWLEDGE",
    7: "BELL",
    8: "BACKSPACE",
    9: "HORIZONTAL TABULATION",
    10: "LINE FEED",
    11: "VERTICAL TABULATION",
    12: "FORM FEED",
    13: "CARRIAGE RETURN",
    14: "SHIFT OUT",
    15: "SHIFT IN",
    16: "DATA LINK ESCAPE",
    17: "DEVICE CONTROL ONE",
    18: "DEVICE CONTROL TWO",
    19: "DEVICE CONTROL THREE",
    20: "DEVICE CONTROL FOUR",
    21: "NEGATIVE ACKNOWLEDGE",
    22: "SYNCHRONOUS IDLE",
    23: "END OF TRANSMISSION BLOCK",
    24: "CANCEL",
    25: "END OF MEDIUM",
    26: "SUBSTITUTE",
    27: "ESCAPE",
    28: "FILE SEPARATOR",
    29: "GROUP SEPARATOR",
    30: "RECORD SEPARATOR",
    31: "UNIT SEPARATOR",
    127: "DELETE"
}

ASCII_CONTROL_CHARS = {
    0: "NUL",
    1: "SOH",
    2: "STX",
    3: "ETX",
    4: "EOT",
    5: "ENQ",
    6: "ACK",
    7: "BEL",
    8: "BS",
    9: "HT",
    10: "LF",
    11: "VT",
    12: "FF",
    13: "CR",
    14: "SO",
    15: "SI",
    16: "DLE",
    17: "DC1",
    18: "DC2",
    19: "DC3",
    20: "DC4",
    21: "NAK",
    22: "SYN",
    23: "ETB",
    24: "CAN",
    25: "EM",
    26: "SUB",
    27: "ESC",
    28: "FS",
    29: "GS",
    30: "RS",
    31: "US",
    127: "DEL"
}

def lookup_unicode(query):
    results = []
    try:
        logger.debug(f"Query: {query}")
        if query.startswith('U+'):
            results.append(lookup_unicode_by_hex_cp(query))
        elif query.isnumeric() and int(query) >= ord(' '):
            results.append(lookup_unicode_by_dec_cp(query))
        elif len(query) == 1:
            results.append(lookup_unicode_by_char(query))
        else:
            results = lookup_unicode_by_name(query)
    except Exception as e:
        results = [{"error": str(e)}]
    logger.debug(f"Results: {results}")
    
    fix_ascii_control_chars(results)
    
    return results


def lookup_unicode_by_hex_cp(query):
    logger.debug("Query is a U+HHHH hex cp")
    cp = int(query[2:], 16)
    char = chr(cp)
    name = get_char_name(char)
    return make_unicode_lookup_result(query, char, cp, name)


def lookup_unicode_by_dec_cp(query):
    logger.debug("Query is a decimal cp")
    cp = int(query)
    char = chr(cp)
    name = get_char_name(char)
    return make_unicode_lookup_result(query, char, cp, name)


def lookup_unicode_by_char(query):
    logger.debug("Query is a single character")
    char = query
    cp = ord(char)
    name = get_char_name(char)
    return make_unicode_lookup_result(query, char, cp, name)


def lookup_unicode_by_name(query):
    logger.debug("Query is a string to search for as part of the name")
    results = []
    for cp in range(0x110000):
        try:
            name = get_char_name(chr(cp))
            if query.upper() in name:
                char = chr(cp)
                result = make_unicode_lookup_result(query, char, cp, name)
                results.append(result)
        except ValueError:
            continue
    return sorted(results, key=lambda x: x["cp"])


def fix_ascii_control_chars(results):
    for result in results:
        cp = result.get("cp")
        if cp in ASCII_CONTROL_CHARS:
            result["name"] = f"<ASCII CONTROL CHARACTER {ASCII_CONTROL_NAMES[cp]}>"
            result["char"] = ASCII_CONTROL_CHARS[cp]


def make_unicode_lookup_result(query, char, cp, name):
    return {
        "query": query,
        "char": char,
        "cp": cp,
        "hex": f"U+{cp:04X}",
        "name": name
    }


def generate_unicode_name_word_cloud():
    logger.info("Generating Unicode name word cloud")

    word_counts = Counter()
    
    for cp in range(0x110000):
        try:
            name = ucd.name(chr(cp))
            name_words = name.split()
            word_counts.update(name_words)
        except ValueError:
            continue


@app.route('/', methods=['GET', 'POST'])
def index():
    query = request.form.get("query", "")
    results = lookup_unicode(query) if query else []
    return render_template('index.html', query=query, results=results)


def get_char_name(char):
    name = ucd.name(char, None)
    if not name:
        cp = ord(char)
        if 0 <= cp <= 31 or cp == 127:
            ascii_name = ASCII_CONTROL_NAMES.get(cp)
            name = f"<ASCII CONTROL CHARACTER {ascii_name}>"
        else:
            name = f"<UNICODE CONTROL CHARACTER U+{cp:04X}>"
    return name


def main():
    parser = argparse.ArgumentParser(description="Run the Unicode lookup app")
    parser.add_argument("--browser", action="store_true",
                        help="Open browser automatically")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    if args.browser:
        Timer(1, open_browser).start()
    
    app.run(debug=True)

    
def open_browser():
    logger.info("Opening browser")
    webbrowser.open_new("http://127.0.0.1:5000/")


if __name__ == '__main__':
    main()
