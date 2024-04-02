#include <iostream>
#include <cstdio>

#include "RegisterMap.hh"
#include "network.hh"
#include "UDPRBCP.hh"
#include "CommandMan.hh"
#include "FPGAModule.hh"
#include "rbcp.h"

using namespace HUL_Scaler;

int main(int argc, char* argv[])
{
  if(1 == argc){
    std::cout << "Usage\n";
    std::cout << "set_nimio [IP address]" << std::endl;
    return 0;
  }// usage
  
  // body ------------------------------------------------------
  char* board_ip = argv[1];
  rbcp_header rbcpHeader;
  rbcpHeader.type = UDPRBCP::rbcp_ver_;
  rbcpHeader.id   = 0;

  FPGAModule fModule(board_ip, udp_port, &rbcpHeader, 0);
  std::cout << fModule.ReadModule(IOM::mid, IOM::laddr_nimout1, 1) << std::endl;
  std::cout << fModule.ReadModule(IOM::mid, IOM::laddr_nimout2, 1) << std::endl;
  std::cout << fModule.ReadModule(IOM::mid, IOM::laddr_nimout3, 1) << std::endl;
  std::cout << fModule.ReadModule(IOM::mid, IOM::laddr_nimout4, 1) << std::endl;
  std::cout << fModule.ReadModule(IOM::mid, IOM::laddr_extL1, 1) << std::endl;
  std::cout << fModule.ReadModule(IOM::mid, IOM::laddr_extL2, 1) << std::endl;
  std::cout << fModule.ReadModule(IOM::mid, IOM::laddr_extClr, 1) << std::endl;
  std::cout << fModule.ReadModule(IOM::mid, IOM::laddr_extSpillGate, 1) << std::endl;
  //  fModule.WriteModule(IOM::mid, IOM::laddr_nimout3, IOM::reg_o_clk1kHz);
  //  std::cout << fModule.ReadModule(IOM::mid, IOM::laddr_nimout3, 1) << std::endl;;
  //  fModule.WriteModule(IOM::mid, IOM::laddr_nimout4, IOM::reg_o_clk1kHz);

  return 0;

}// main
