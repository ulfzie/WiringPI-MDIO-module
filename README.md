# WiringPI-MDIO-module
This module helps to access PHY registers over MDIO. It is designed to be used with a Raspberry Pi and the wiringpi library.

## Installation

On Raspberry Pi open a shell and type

```
sudo apt install python-pip 
sudo pip install wiringpi2
```

I tested it with an RPi2 and connected the cables this way:

1. MDIO on pin 9 and MDC on pin 8
2. MDIO on pin 25 and MDC on pin 24

For a graphic please see the [Raspberry Pi B++ Leaf](https://github.com/splitbrain/rpibplusleaf) and use the gray numbers!


## Usage

```python
from mdio import MDIO
import logging as log

PHYADDR = 24

mc = MDIO(mdcpin = 8,mdiopin = 9)
mc.ResetPhy(phyAddr = PHYADDR)
if mc.CheckPhy(phyAddr = PHYAD_BR,r2 = 0x0362,r3 = 0x5cc6):
	log.critical("Could not find BCM54811!")
	exit()
	
mc.WriteRegister(phyAddr = PHYAD_BR, regAddr = 0x00, value = 0x1000)

while mc.CheckLink(PHYAD_BR) == 0:
	pass

```

## Test
Code was tested with BCM54811 and the basic functions should run on all PHY supporting clause 22.