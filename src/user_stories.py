import cgi
import yaml
import itertools
import re
import argparse
import sys


page_templ = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->

<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   width="1052.3622"
   height="744.09448"
   id="svg2"
   version="1.1"
   inkscape:version="0.48.4 r9939"
   sodipodi:docname="story_sample.svg">
  <defs
     id="defs4" />
  <sodipodi:namedview
     id="base"
     pagecolor="#ffffff"
     bordercolor="#666666"
     borderopacity="1.0"
     inkscape:pageopacity="0.0"
     inkscape:pageshadow="2"
     inkscape:zoom="0.941691"
     inkscape:cx="386.25916"
     inkscape:cy="526.18109"
     inkscape:document-units="px"
     inkscape:current-layer="layer1"
     showgrid="false"
     units="mm"
     inkscape:window-width="1920"
     inkscape:window-height="1178"
     inkscape:window-x="1912"
     inkscape:window-y="-8"
     inkscape:window-maximized="1" />
  <metadata
     id="metadata7">
    <rdf:RDF>
      <cc:Work
         rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
           rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title></dc:title>
      </cc:Work>
    </rdf:RDF>
  </metadata>
  <g
     inkscape:label="Layer 1"
     inkscape:groupmode="layer"
     id="layer1">
     %(rects)s
     %(stories)s
     %(sizes)s
  </g>
</svg> 
"""


story_rect_templ = """    <rect
       style="fill:%(color)s;fill-opacity:1"
       id="%(id_)s"
       width="490"
       height="335"
       x="%(x)f"
       y="%(y)f" />
"""


story_text_templ = """<flowRoot
       xml:space="preserve"
       id="%(root_id)s"
       style="font-size:32px;font-style:normal;font-weight:normal;
       line-height:125%%;letter-spacing:0px;word-spacing:0px;
       fill:#000000;fill-opacity:1;stroke:none;font-family:Sans"
       ><flowRegion
         id="%(region_id)s"><rect
           id="rect5655"
           width="480"
           height="335"
           x="%(x)f"
           y="%(y)f" /></flowRegion><flowPara id="%(para_id)s">%(main_text)s</flowPara>%(acc_crit_list)s</flowRoot>
"""


big_repl = r"""\1<flowSpan
   style="font-size:40px;font-weight:bold"
   id="%s">\2</flowSpan>\3"""


big_pat = r"(\W)_([^_]+)_(\W)"


story_acc_crit_templ = """<flowPara
         id="%(id_)s"
         style="font-size:12px"> - %(text)s</flowPara>"""


story_size_templ = """<text
       xml:space="preserve"
       style="font-size:24px;font-style:normal;font-weight:normal;line-height:125%%;letter-spacing:0px;word-spacing:0px;fill:#000000;fill-opacity:1;stroke:none;font-family:Sans"
       x="%(x)f"
       y="%(y)f"
       id="%(text_id)s"
       sodipodi:linespacing="125%%"><tspan
         sodipodi:role="line"
         id="%(tspan_id)s"
         x="%(x)f"
         y="%(y)f"
         style="font-size:40px">%(size)s</tspan></text>"""


ID = 5000
def get_id(prefix):
    global ID
    ID += 1
    return "%s%i" % (prefix, ID)


def make_rect(x, y):
    return story_rect_templ % dict(
        color='#ecff8c', 
        id_=get_id('rect'), 
        x=x, 
        y=y)


def make_story(x, y, story):
    acc_crit_list = []
    for acc_crit in story.acc_crit_list:
        acc_crit_list.append(story_acc_crit_templ % dict(
            id_=get_id('flowPara'), 
            text=cgi.escape(acc_crit)))
    main_text=re.sub(big_pat, 
                     big_repl % get_id('flowSpan'),
                     cgi.escape(story.main_text))
    story_text = story_text_templ % dict(
        root_id=get_id('flowRoot'),
        region_id=get_id('flowRegion'),
        x=x,
        y=y,
        para_id=get_id('flowPara'),
        main_text=main_text,
        acc_crit_list="".join(acc_crit_list)
        )
    return story_text


def make_size(x, y, story):
    return story_size_templ % dict(
        size=story.size,
        x = x,
        y = y,
        text_id = get_id('text'),
        tspan_id = get_id('tspan'),
    )


def make_page(fn, stories):
    rect_list = []
    story_list = []
    size_list = []
    positions = [(30, 30), (540, 30), (30, 385), (540, 385)]
    for pos, story in zip(positions, stories):
        story = Story(story)
        rect_list.append(make_rect(pos[0], pos[1]))
        story_list.append(make_story(pos[0] + 5, pos[1] + 5, story))
        size_list.append(make_size(pos[0] + 440, pos[1] + 325, story))
    text = page_templ % dict(
        rects='\n'.join(rect_list),
        stories='\n'.join(story_list),
        sizes='\n'.join(size_list),
    )
    f = open(fn, 'w')
    f.write(text)
    f.close()


class Story(object):
    def __init__(self, entry):
        self.main_text = entry['main_text']
        self.acc_crit_list = entry.get('acc_crit_list', [])
        self.size = entry.get('size', '?')


def get_chunk(size, sequence):
    res = sequence[:size]
    del sequence[:size]
    return res


def parse_args(args):
  parser = argparse.ArgumentParser(description="Turn YAML stories into .svg for printing.")
  parser.add_argument('source', help='YAML source file')
  parser.add_argument('-s', '--sprint', help="select stories for a certain sprint")
  parser.add_argument(
    '-p', '--prefix', 
    default = 'page',
    help="beginning of output file names")
  return parser.parse_args(args)


def main(args):
    parser = parse_args(args)
    stories = yaml.load(open(parser.source))
    if parser.sprint:
      stories = (story for story in stories if parser.sprint in story['sprint'])
    story_list = list(stories)
    page = 1
    while 1:
        chunk = get_chunk(4, story_list)
        if not chunk:
            break
        make_page('%s%i.svg' % (parser.prefix, page), chunk)
        page += 1


if __name__ == '__main__':
  main(sys.argv[1:])