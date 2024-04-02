#include <iostream>
#include <cstdio>

#include "RegisterMap.hh"
#include "network.hh"
#include "UDPRBCP.hh"
#include "CommandMan.hh"
#include "FPGAModule.hh"
#include "rbcp.h"
#include "BitDump.hh"

using namespace HUL_Scaler;
int main(int argc, char* argv[])
{
  if(1 == argc){
    std::cout << "Usage\n";
    std::cout << "hul_main [IP address]" << std::endl;
    return 0;
  }// usage
  
  // body ------------------------------------------------------
  char* board_ip = argv[1];
  rbcp_header rbcpHeader;
  rbcpHeader.type = UDPRBCP::rbcp_ver_;
  rbcpHeader.id   = 0;

  FPGAModule fModule(board_ip, udp_port, &rbcpHeader, 0);
  std::cout << std::hex << fModule.ReadModule(BCT::mid, BCT::laddr_Version, 4) << std::endl;

  //  unsigned int reg = fModule.ReadModule(MTM::mid, MTM::laddr_sel_trig, 2);
  //  hddaq::BitDump dump;
  //  dump(reg);

  return 0;

}// main
