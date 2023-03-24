; VERY SHORT sample extracted of sample 1
; Laser is only 1% so visual only but not burning anything (S010 = 01.0%)

; LightBurn 1.3.01
; GRBL device profile, absolute coords
; Bounds: X8 Y4.6 to X83.13 Y24.9
G00 G17 G40 G21 G54
G90
M4
; Cut @ 30 mm/sec, 60% power
M8
G0 X8Y8
; Layer border (made it 1%)
G1 Y23S010F1800
G1 X23
G1 Y8
G1 X8
G0 X46.762Y14.891
G1 X50.762Y21.82
G1 X58.762
G1 X62.762Y14.891
G1 X58.762Y7.963
G1 X50.762
G1 X46.762Y14.891
G90
M9
G1 S0
M5
G90
; return to user-defined finish pos
G0 X0 Y0
M2
