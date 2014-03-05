"""Move mouse on a mac

http://stackoverflow.com/questions/281133/controlling-the-mouse-from-python-in-os-x
"""

#!/usr/bin/python

import sys

def setMousePosition(x, y):
    if sys.platform == "linux2":
        import subprocess
        subprocess.call(['xdotool', 'mousemove', str(x), str(y)])
    elif sys.platform == "darwin": 
        import objc
        bndl = objc.loadBundle('CoreGraphics', globals(),
            '/System/Library/Frameworks/ApplicationServices.framework')
        objc.loadBundleFunctions(bndl, globals(),
            [('CGWarpMouseCursorPosition', 'v{CGPoint=dd}')])
        CGWarpMouseCursorPosition((x, y)) 


if __name__ == "__main__":
    setMousePosition(200, 200)