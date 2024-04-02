#ifndef SITCPCTRL_
#define SITCPCTRL_

#include"rbcp.h"
#include"network.hh"

void Reset_SiTCP(const char* ip, rbcp_header* header);

void Write_SiTCP(const char* ip, rbcp_header* header,
		 unsigned int addr_ofs, unsigned int reg);
void Read_SiTCP(const char* ip, rbcp_header* header,
		unsigned int addr_ofs);

void Erase_EEPROM(const char* ip, rbcp_header* header);

#endif
