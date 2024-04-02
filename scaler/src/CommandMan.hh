#ifndef COMMANDMAN_
#define COMMANDMAN_

#include"Uncopyable.hh"

struct rbcp_header;

class CommandMan
  : Uncopyable<CommandMan>
{
  static const int max_line_length_  = 1024;
  static const int max_param_length_ = 20;

public:
  int parse_rbcp_command();

  CommandMan(char* ipAddr, unsigned int port, rbcp_header* sendHeader);
  virtual ~CommandMan();

private:
  char*        ipAddr_;
  unsigned int port_;
  rbcp_header *sendHeader_;

  int DispatchCommand(char* pszVerb, char* pszArg1, char* pszArg2);
		      
  int OnHelp();
};

#endif
