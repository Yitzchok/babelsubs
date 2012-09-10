import re
import bleach
import htmllib
import formatter

from itertools import chain

DEFAULT_ALLOWED_TAGS = ['i', 'b', 'u']
MULTIPLE_SPACES = re.compile('\s{2,}')
BLANK_CHARS = re.compile('[\n\t\r]*')

def unescape_html(s):
    p = htmllib.HTMLParser(formatter.NullFormatter() )
    # we need to preserve line breaks, nofill makes sure we don't
    # loose them
    p.nofill = True
    p.save_bgn()
    p.feed(s)
    return p.save_end().strip()

LANG_DIALECT_RE = re.compile(r'(?P<lang_code>[\w]{2,13})(?P<dialect>-[\w]{2,8})?(?P<rest>-[\w]*)?')

def to_bcp47(code):
    """
    This is an ugly hack. I should be ashamed, but I'm not.
    Implementing BCP47 will be much more work.
    The idea is to translate from a lang code unilangs supports
    into the bpc47 format. There are cases where this might fail
    (as if the dialect code is not recognized by bcp47). For most cases this should be ok.

    Simple sanity chech:
    assert (unilangs.to_bcp47("en-us"), unilangs.to_bcp47('en'), unilangs.to_bcp47('ug_Arab-cn')) == ('en-US', 'en', 'ug_Arab-CN'
)
    """
    if not code:
         raise ValueError("No language was passed")

    match = LANG_DIALECT_RE.match(code)
    if not match:
         raise ValueError("%s code does not seem to be a valid language code.")

    match_dict = match.groupdict()
    return "%s%s%s" % (match_dict['lang_code'],
                       (match_dict.get('dialect', "") or "").upper(),
                       match_dict.get('rest', '') or "")

def generate_style_map(dom):
    '''
    Parse the head.styling node on the xml and generate a hash -> list
    of styles that require our supported formatting optins (bold and
    italic for now).
    eg.
    style_map = {
        'italic': ['speaker', 'importante'],
        'bold': [],
    }
    This will be used when parsing each text node to make sure
    we can convert to our own styling markers.
    '''
    style_map = {
        'italic': [],
        'bold': [],
    }
    styling_nodes = dom.getElementsByTagName("styling")
    style_nodes = chain.from_iterable([x.getElementsByTagName('style') for x in styling_nodes])
    for style_node in style_nodes:
        style_id = style_node.getAttribute('xml:id')
        for key in style_node.attributes.keys():
            value  = style_node.attributes[key].value
            if key  == 'tts:fontWeight' and  value == 'bold':
                style_map['bold'].append(style_id)
            elif key  == 'tts:fontStyle' and value == 'italic':
                style_map['italic'].append(style_id)
    return style_map

def strip_tags(text, tags=None):
    """
    Returns text with the tags stripped.
    By default we allow the standard formatting tags
    to pass (i,b,u).
    Any other tag's content will be present, but with tags removed.
    """
    if tags is None:
        tags = DEFAULT_ALLOWED_TAGS
    return bleach.clean(text, tags=tags, strip=True)

def from_xmlish_text(input_str):
    """
    Parses text content from xml based formats.
    <br> tags are transformed into newlines, tab and multiple spaces
    collapsed. e.g. turns:
    "\n\r foo  <br/> bar foorer \t " -> "foo bar\nfoorer"
    """
    if not input_str:
        return u""
    # remove new lines and tabs
    input_str = BLANK_CHARS.sub(u"", input_str)
    # do convert <br> to new lines
    input_str = input_str.replace("<br/>", "\n")
    # collapse whitespace on each new line
    return "\n".join( MULTIPLE_SPACES.sub(u" ", x).strip() for x in input_str.split('\n'))

def milliseconds_to_time_clock_components(milliseconds):
    """
    Converts milliseconds (as an int) to the
    hours, minutes, seconds and milliseconds.
    None will be converted to all zeros
    """
    components = dict(hours=0, minutes=0, seconds=0, milliseconds=0)

    if milliseconds is not None:
        components['seconds'], components['milliseconds'] = divmod(int(milliseconds), 1000)
        components['minutes'], components['seconds'] = divmod(components['seconds'], 60 )
        components['hours'], components['minutes'] = divmod(components['minutes'], 60 )

    return components
