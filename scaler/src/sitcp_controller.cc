#include"sitcp_controller.hh"
#include"errno.h"
#include"UDPRBCP.hh"

#include<iostream>
#include<cstdio>
#include<csignal>
#include<string>

static const unsigned int addr_base       = 0xffffff00;
static const unsigned int addr_ctrl_sitcp = 0x10;

static const unsigned int c_sitcp_reset   = 0x80;
static const unsigned int c_keep_alive    = 0x04;
static const unsigned int c_fast_retrains = 0x02;
static const unsigned int c_nagle_buffer  = 0x01;

// Reset SiTCP -------------------------------------------------------------
void
Reset_SiTCP(const char* ip, rbcp_header* header)
{
  UDPRBCP udpMan(ip, udp_port, header);
  unsigned int addr   = addr_base + addr_ctrl_sitcp;
  unsigned int wd_def = c_nagle_buffer; // default;
  unsigned int wd     = wd_def + c_sitcp_reset;

  std::cout << "#D : ##### SiTCP Controll #####" << std::endl;
  std::cout << "#D : Trying Reset SiTCP" 
	    << std::endl; 

  udpMan.SetWD(addr, 1, (char*)&wd);
  udpMan.DoRBCP();

  udpMan.SetWD(addr, 1, (char*)&wd_def);
  udpMan.DoRBCP();
}

// Write SiTCP -------------------------------------------------------------
void
Write_SiTCP(const char* ip, rbcp_header* header,
	    unsigned int addr_ofs, unsigned int reg)
{
  UDPRBCP udpMan(ip, udp_port, header);
  unsigned int addr   = addr_base + addr_ofs;

  std::cout << "#D : ##### SiTCP Controll #####" << std::endl;
  std::cout << std::hex 
	    << "#D : Trying Write Register (" << reg << ") to Address (" << addr << ")" 
	    << std::dec << std::endl; 

  udpMan.SetWD(addr, 1, (char*)&reg);
  udpMan.DoRBCP();
}

// Read SiTCP  -------------------------------------------------------------
void
Read_SiTCP(const char* ip, rbcp_header* header,
	   unsigned int addr_ofs)
{
  UDPRBCP udpMan(ip, udp_port, header);
  unsigned int addr   = addr_base + addr_ofs;

  std::cout << "#D : ##### SiTCP Controll #####" << std::endl;
  std::cout << std::hex 
	    << "#D : Trying Read Register from Address (" << addr << ")" 
	    << std::dec << std::endl; 

  udpMan.SetRD(addr, 1);
  udpMan.DoRBCP();
}

// Erase EEPROM ------------------------------------------------------------
void
Erase_EEPROM(const char* ip, rbcp_header* header)
{
  std::cout << "#D : ##### SiTCP Controll #####" << std::endl;
  std::cout << "#D : Trying Erase EEPROM" 
	    << std::endl; 

  UDPRBCP udpMan(ip, udp_port, header, UDPRBCP::disp_no);
  unsigned int addr = 0xfffffcff;
  unsigned int wd   = 0x0;
  udpMan.SetWD(addr, 1, (char*)&wd);
  udpMan.DoRBCP();
  std::cout << "#D : Waiting" << std::flush;
  sleep(1);

  // fill 128byte from 0xfffffc00 with 0xff 
  addr = 0xfffffc00;
  wd   = 0xff;
  for(unsigned int i = 0; i<128; ++i){
    std::cout << "." << std::flush;
    udpMan.SetWD(addr+i, 1, (char*)&wd);
    udpMan.DoRBCP();
    sleep(1);
    
  }// for(i)
  std::cout << std::endl;
  std::cout << "#D : Finish Erase EEPROM" << std::endl;
}
