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
  char board_ip[] = "192.168.10.136";
  rbcp_header rbcpHeader;
  rbcpHeader.type = UDPRBCP::rbcp_ver_;
  rbcpHeader.id   = 0;

  FPGAModule fModule(board_ip, udp_port, &rbcpHeader);
  fModule.WriteModule(BCT::mid, BCT::laddr_ReConfig, 0);

  return 0;
}// main
