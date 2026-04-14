# xTool UV Laser integration

## External Fan 
xTool must turn on external exhaust fan in room when badged-in.
xTool UV drives into the SAME relay to control external fan power as the MOPA. 
Therefore ground and +5v relay input signal come FROM MOPA laser. xTool RATT must drive this signal
high to turn relay on. As MOPA RATT is doing the same, each has diodes on their +5v logic lines
to prevent backfeeding the other.

# xTool Activity
xTool activity is determined by a signal coming from it's internal fan. As this fan is a removable
module, it presented with the simplest integration point. The BLUE WIRE on this fan is PWM
signal used to turn the fan on. This line is normally idle (zero voles) - but when the laser
is in-use (fan is on) - is appears to be a +/-2 v 1kHz square wave (PWM signal). 

Because it would be difficult for RATT itself to detect when this signal is present, we create
a separate buffer board which closes a connection to ground for the RATT input (optisolator).
i.e. RATT inputs for this signal are +5 and a connection to fan buffer board.

# Fan Buffer
`UVswitch.txt` is a simulator for Falstead Circuit Simulator - see this board at [falstead](https://www.falstad.com/circuit/circuitjs.html?ctz=DwYwlgTgBAZgvAIgIwKgFwM6IAwDpsEECsqYIiAzABwBMuA7AGw1G1IAsFAnF9o+6hAAjRJ1QAHEQiLZUANwiIaqALaZERAKYBaJCgB8AKChRgAdygAPSkRpQaNdlAq2oSJqnjIEAeiMngADUAQwgAJWCwABsrGzsuRmdXXUZPHFQzL3pPRWlVYMs5DVQMNEQAYQB7KKjNEDRK6EDqtGCAc01ff1M22IQXO3YkRIGoTmVYdL9jUzQ+imwnR2wku2W0hFkocQA7RBQoIU19glVKxAATTRhggFcotHkjxG0KXFYqJCoKenoaLhov2oT3Im1wnHoXG4Q2wAM4jFhJGmATCfSoK2WbkS60myFSUEyShyJ1OUBUBSKCGUyNMFz6NGwVHs7BWCyWLI2WxU52QADkhuwqF0ZsBoNZkOx2RjGcytl4trkkIRZDTQPNFrLnBqKAzOYIcPhlTxjSbTTxSJS8AQDhhcls5BcDRCoVwYXCKAiuEjusBeuK2c4GVqnAM9aqADIAUQAIvNXAlVm4PLiuTyrjd7mhtLULoJFYI2ukoMIiyohKCrShVRZ-a4WCNXEN8fLhQEMGiMSy3JLZXrtvthcAfOAIEYgA) 

# Files
`UV Activity Buffer.svg` and `UV Activity Buffer_ART.svg` are laserable designs for Fan buffer PCB.

