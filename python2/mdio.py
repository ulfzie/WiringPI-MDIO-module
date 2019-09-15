"""
This module helps to access PHY registers over MDIO.
It is designed to be used with a Raspberry Pi and the wiringpi library
"""

import wiringpi
import logging

wiringpi.wiringPiSetup() # For GPIO pin numbering


class MDIO(object):
	def __init__(self,mdiopin,mdcpin):
		"""
		Set the pins used for MDIO and MDC.
		See gray numbers in https://github.com/splitbrain/rpibplusleaf 

		Args:
			mdiopin (int): pin number on RPi (range 1 - 31)
			mdcpin (int):  pin number on RPi (range 1 - 31)
		"""
		self.MDIO = mdiopin
		self.MDC = mdcpin
		# Set pin to output
		wiringpi.pinMode(self.MDIO,wiringpi.GPIO.OUTPUT)
		wiringpi.pinMode(self.MDC,wiringpi.GPIO.OUTPUT) 


	def Write(self,value):
		""" 
		Writes a single bit on the MDC
		Args:
			value: 0 or 1
		"""
		logging.debug("Write: %i",value)
		wiringpi.digitalWrite(self.MDIO,value)
		wiringpi.digitalWrite(self.MDC,1)
		wiringpi.digitalWrite(self.MDC,0)

	def ReadRegister(self,phyAddr, regAddr):
		"""
		Reads a register from the PHY
		Args:
			phyAddr: PHY address
			regAddr: Register address
		Result:
			read 16bit width int value 
		"""
		logging.info("ReadRegister: PHY: 0x%02x Addr:0x%02x",phyAddr, regAddr)
		wiringpi.digitalWrite(self.MDC,0)
		wiringpi.pinMode(self.MDIO,wiringpi.GPIO.OUTPUT) 
		
		for x in range(37):
			self.Write(1)
			
		# START
		self.Write(0)
		self.Write(1)
		# READ
		self.Write(1)
		self.Write(0)
		
		# Write 5 bits of PHY addr
		for x in range(5):
			if phyAddr & 0x10:
				self.Write(1)
			else:
				self.Write(0)
			phyAddr = phyAddr << 1

		# Write 5 bits of REG addr
		for x in range(5):
			if regAddr & 0x10:
				self.Write(1)
			else:
				self.Write(0)
			regAddr = regAddr << 1

		# Set MDIO to input
		wiringpi.pinMode(self.MDIO,wiringpi.GPIO.INPUT)
		# Wait for turnaround bits
		wiringpi.digitalWrite(self.MDC,1)
		wiringpi.digitalWrite(self.MDC,0)
		wiringpi.digitalWrite(self.MDC,1)
		wiringpi.digitalWrite(self.MDC,0)
		
		# Read 16 bits of data
		result = 0
		for i in range(16):
			result = result << 1
			result = result | wiringpi.digitalRead(self.MDIO)
			wiringpi.digitalWrite(self.MDC,1)
			wiringpi.digitalWrite(self.MDC,0)
		
		logging.info("ReadRegister: Value: 0x%04x",result)
		return result

	def WriteRegister(self,phyAddr, regAddr, value):
		"""
		Writes to a register a value
		Args:
			phyAddr(int): PHY address
			regAddr(int): Register address
			value(int): Value to write into specified register
		"""
		logging.info("WriteRegister: PHY: 0x%02x Addr:0x%02x Value: 0x%04x",phyAddr, regAddr, value)

		wiringpi.digitalWrite(self.MDC,0)
		wiringpi.pinMode(self.MDIO,wiringpi.GPIO.OUTPUT) 

		for x in range(37):
			self.Write(1)

		# START
		self.Write(0)
		self.Write(1)
		# WRITE
		self.Write(0)
		self.Write(1)
		# Write 5 bits of PHY addr
		for x in range(5):
			if phyAddr & 0x10:
				self.Write(1)
			else:
				self.Write(0)
			phyAddr = phyAddr << 1

		# Write 5 bits of REG addr
		for x in range(5):
			if regAddr & 0x10:
				self.Write(1)
			else:
				self.Write(0)
			regAddr = regAddr << 1

		# Turnaround bits
		self.Write(1)
		self.Write(0)
		
		# Write 16 bits of data
		for i in range(16):
			if value & 0x8000:
				self.Write(1)
			else:
				self.Write(0)
			value = value << 1
		
		wiringpi.pinMode(self.MDIO,wiringpi.GPIO.INPUT) 
		wiringpi.digitalWrite(self.MDC,0)

	def WriteExpansionRegister(self,phyAddr, regAddr, value):
		"""
		Writes to an expansion register a value
		Args:
			phyAddr(int): PHY address
			regAddr(int): Register address
			value(int): Value to write into specified register
		"""
		self.WriteRegister(phyAddr = phyAddr , regAddr = 0x17, value = regAddr | 0x0F00)
		self.WriteRegister(phyAddr = phyAddr , regAddr = 0x15, value = value)
		self.WriteRegister(phyAddr = phyAddr , regAddr = 0x17, value = 0x0000)

	def ReadExpansionRegister(self,phyAddr, regAddr):
		"""
		Reads a register and returns the value
		Args:
			phyAddr(int): PHY address
			regAddr(int): Register address
		Result:
			value read from register		
		"""

		self.WriteRegister(phyAddr = phyAddr , regAddr = 0x17, value = regAddr | 0x0F00)
		result = self.ReadRegister(phyAddr = phyAddr , regAddr = 0x15)
		self.WriteRegister(phyAddr = phyAddr , regAddr = 0x17, value = 0x0000)
		return result
	
	def CheckPhy(self, phyAddr, r2 , r3):
		"""
		This function reads the chip ID from register 0x02 and 0x03 and compares 
		it with the given values. Check data sheet for default value
		Args:
			phyAddr(int): PHY address
			r2(int): expected value from register 0x02
			r3(int): expected value from register 0x03
		Result:
			0 - PHY detected
			1 - IDs do not match
		"""
		if self.ReadRegister(phyAddr = phyAddr, regAddr = 0x02) != r2:
			return 1
		if self.ReadRegister(phyAddr = phyAddr, regAddr = 0x03) != r3:
			return 1
		return 0

	def ResetPhy(self, phyAddr):
		"""
		Reset the PHY.
		Args:
			phyAddr(int): PHY address
		"""
		self.WriteRegister(phyAddr = phyAddr, regAddr = 0x00, value = 0x8000)
		while self.ReadRegister(phyAddr = phyAddr, regAddr = 0x00) & 0x8000:
			logging.warning(".")

		return 0
	def CheckLink(self, phyAddr):
		"""
		This function returns the link state of the PHY
		Args:
			phyAddr(int): PHY address
		Result:
			0 - Link down
			1 - Link up
		"""
		
		if self.ReadRegister(phyAddr = phyAddr, regAddr = 0x01) & 0x0004:
			return 1
		else:
			# Remove latched value
			return (self.ReadRegister(phyAddr = phyAddr, regAddr = 0x01) & 0x0004) / 0x0004


if __name__ == '__main__':
	print("This only executes when %s is executed rather than imported" % __file__)
