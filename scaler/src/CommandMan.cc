#include"CommandMan.hh"
#include"myString.hh"
#include"UDPRBCP.hh"
#include"rbcp.h"

#include<iostream>
#include<cstdio>
#include<cstdlib>
#include<cstring>

CommandMan::CommandMan(char* ipAddr,
		       unsigned int port,
		       rbcp_header* sendHeader)
  :
  ipAddr_(ipAddr),
  port_(port),
  sendHeader_(sendHeader)
{
  
}

CommandMan::~CommandMan()
{

}

int CommandMan::parse_rbcp_command()
{
  char tempKeyBuf[myString::max_line_length_];
  char szVerb[myString::max_param_length_];
  char szArg1[myString::max_param_length_];
  char szArg2[myString::max_param_length_];
  int  rtnValue = 0;
  
  std::cout << "SiTCP-RBCP$ " << std::flush;
  fgets(tempKeyBuf, myString::max_line_length_, stdin);
  if((rtnValue = myString::myScanf(tempKeyBuf,szVerb, szArg1, szArg2)) < 0 ){
    std::cerr << "Error myString::myScanf() : " << rtnValue << std::endl;
    return -1;
  }
  
  ++sendHeader_->id;
  
  return DispatchCommand(szVerb, szArg1, szArg2);
  
}

int CommandMan::DispatchCommand(char* pszVerb,
				char* pszArg1,
				char* pszArg2
				){
  UDPRBCP uMan(ipAddr_, port_, sendHeader_);

  unsigned int tempInt;

  if(strcmp(pszVerb, "wrb") == 0){
    tempInt = myString::myAtoi(pszArg2);
    pszArg2[0]= (char)(0xFF & tempInt);

    uMan.SetWD(myString::myAtoi(pszArg1), 1, pszArg2);

    return uMan.DoRBCP();
  }
  else if(strcmp(pszVerb, "wrs") == 0){
    tempInt = myString::myAtoi(pszArg2);
    pszArg2[1]= (char)(0xFF & tempInt);
    pszArg2[0]= (char)((0xFF00 & tempInt)>>8);

    uMan.SetWD(myString::myAtoi(pszArg1), 2, pszArg2);

    return uMan.DoRBCP();
  }
  else if(strcmp(pszVerb, "wrw") == 0){
    tempInt = myString::myAtoi(pszArg2);

    pszArg2[3]= (char)(0xFF & tempInt);
    pszArg2[2]= (char)((0xFF00 & tempInt)>>8);
    pszArg2[1]= (char)((0xFF0000 & tempInt)>>16);
    pszArg2[0]= (char)((0xFF000000 & tempInt)>>24);

    uMan.SetWD(myString::myAtoi(pszArg1), 4, pszArg2);

    return uMan.DoRBCP();
  }
  else if(strcmp(pszVerb, "rd") == 0){
    uMan.SetRD(myString::myAtoi(pszArg1), myString::myAtoi(pszArg2));

    return uMan.DoRBCP();
  }
  else if(strcmp(pszVerb, "help") == 0){
    return OnHelp();
  }
  else if(strcmp(pszVerb, "quit") == 0){
    return -1;
  }
  std::cout << "No such command!" << std::endl;
  return 0;
    
}

int CommandMan::OnHelp()
{
  std::cout << "Command list:\n"
	    << "   wrb [address] [byte_data] : Write byte\n"
	    << "   wrs [address] [short_data]: Write short(16bit)\n"
	    << "   wrw [address] [word_data] : Write word(32bit)\n"
	    << "   rd [address] [length]     : Read data\n"
	    << "   load [file name]          : Execute a script\n"
	    << "   quit                      : quit from this program\n" 
	    << std::endl;
  
  return 0;
}
