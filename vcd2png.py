#!/usr/bin/python
import sys
from pyvirtualdisplay.smartdisplay import SmartDisplay, DisplayTimeoutError
from easyprocess import EasyProcess
from PIL import ImageFilter
import os
import tempfile
from  path import Path

"""
adapted from sphinxcontrib.gtkwave (https://github.com/ponty/sphinxcontrib-gtkwave)
    Workaround for missing GTKWAVE export png functionality. Takes a screenshot of GtkWave running on a dummy x11 server.
"""

def get_black_box(im):
    im3 = im.point(lambda x: 255 * bool(x))
    im2 = im3.filter(ImageFilter.MaxFilter(3))
    im5 = im2.point(lambda x: 255 * bool(not x))
    bbox = im5.getbbox()
    # ignore_black_parts
    im6 = im.crop(bbox)
    bbox2 = im6.getbbox()
    if bbox and bbox2:
        bbox3 = (bbox[0] + bbox2[0],
                 bbox[1] + bbox2[1],
                 bbox[0] + bbox2[2],
                 bbox[1] + bbox2[3],

                 )
        return bbox3


def prog_shot(cmd, f, wait, timeout, screen_size, visible, bgcolor):
    '''start process in headless X and create screenshot after 'wait' sec.
    Repeats screenshot until it is not empty if 'repeat_if_empty'=True.

    wait: wait at least N seconds after first window is displayed,
    it can be used to skip splash screen

    :param wait: int
    '''

    def cb_imgcheck(img):
        """accept img if height > minimum."""
        rec = get_black_box(img)
        if not rec:
            return False
        left, upper, right, lower = rec
        accept = lower - upper > 30  # pixel
        print('cropped img size={},{},{},{} accepted={}'.format(left, upper, right, lower, accept))
        return accept

    with  SmartDisplay(visible=visible, size=screen_size, bgcolor=bgcolor, backend='xvfb') as disp:
     with EasyProcess(cmd) as proc:
        if wait:
            proc.sleep(wait)
        try:
            img = disp.waitgrab(timeout=timeout, cb_imgcheck=cb_imgcheck)
        except DisplayTimeoutError as e:
            raise DisplayTimeoutError(str(e) + ' ' + str(proc))

    if img:
        bbox = get_black_box(img)
        assert bbox
        # extend to the left side
        bbox = (0, bbox[1], bbox[2], bbox[3])
        img = img.crop(bbox)

        img.save(f)
    return (proc.stdout, proc.stderr)


images_to_delete = []
image_id = 0

class GtkWaveWrapper(object):
    def __init__(self) :
        self._tcl = r'''
set clk48 [list]

set nfacs [ gtkwave::getNumFacs ]
for {set i 0} {$i < $nfacs } {incr i} {
set facname [ gtkwave::getFacName $i ]

# set fields [split $facname "\\"]
# set sig [ lindex $fields 1 ]
set fields [split $facname "\\"]
set sig1 [ lindex $fields 0 ]
set sig2 [ lindex $fields 1 ]
if {[llength $fields]  == 2} {
set sig "$sig2"
} else {
set sig "$sig1"
}

lappend clk48 "$sig"
}

set num_added [ gtkwave::addSignalsFromList $clk48 ]

set max_time [ gtkwave::getMaxTime ]
set min_time [ gtkwave::getMinTime ]

gtkwave::setZoomRangeTimes $min_time $max_time
'''
        self._rc = r'''
hide_sst 1
splash_disable 1
enable_vert_grid 0

'''
    def run(self, vcdFilename):

        with tempfile.TemporaryDirectory(prefix='gtkwave') as tmpdirname:
            tclfile = Path(tmpdirname) / 'gtkwave.tcl'
            tclfile.write_text(self._tcl)

            rcfile = Path(tmpdirname) / 'gtkwave.rc'
            rcfile.write_text(self._rc)

            cmd = ['gtkwave',
                '--nomenu',
                '--script',
                tclfile,
                vcdFilename,
                rcfile,
                ]
            f = 'gtkwave_{}.png'.format(os.path.splitext(os.path.basename(vcdFilename))[0])
            fabs = Path(vcdFilename).dirname() / (f)
            images_to_delete.append(fabs)

            prog_shot(cmd, fabs, screen_size=(1024,768), wait=0,
                    timeout=12, visible=True, bgcolor='white')
            print('Saved screenshot of {} in {}'.format(vcdFilename, fabs))


if __name__ == "__main__" : 
    wrapper = GtkWaveWrapper()
    wrapper.run(sys.argv[1])
