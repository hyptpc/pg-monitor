#include<fstream>
#include<cstdlib>
#include<sys/time.h>
#include <iostream>
#include <string>
#include <cstring>
#include <fstream>
#include <sstream>
#include <signal.h>
#include <vector>
#include <iomanip>

#include"daq_funcs.hh"
#include "postgresql_helper.hh"

bool user_stop = false;

static const int NofHead = 3;
static const int NofBody = 256;
static const int NofData = NofHead + NofBody;
static const int print_step = 1;
const int header_size = 3;
const int U_ch_size = 32;
const int D_ch_size = 32;

using namespace HUL_Scaler;
#define COMPRESS 0

// signal -----------------------------------------------------------------
void
UserStop_FromCtrlC(int signal)
{
  std::cout << "Stop request" << std::endl;
  user_stop = true;
}

// execute daq ------------------------------------------------------------
void
//daq(char* ip, rbcp_header *rbcpHeader, int runno, int eventno)
daq(char* ip, rbcp_header *rbcpHeader)
{
  ::signal(SIGINT, UserStop_FromCtrlC);

  std::map<int, unsigned long long> scaler_map;

  // TCP socket
  int sock;
  if(-1 == (sock = ConnectSocket((const char*)ip))) return;
  std::cout << "socket connected" << std::endl;

  FPGAModule fModule(ip, udp_port, rbcpHeader, 0);  

  // set sel trig
  //  unsigned int sel_trig = TRM::reg_L1RM | TRM::reg_L2RM | TRM::reg_EnRM | TRM::reg_EnL2;
  //  unsigned int sel_trig = TRM::reg_L1J0 | TRM::reg_L2J0 | TRM::reg_EnJ0 | TRM::reg_EnL2;
  //  unsigned int sel_trig = TRM::reg_L1Ext;
  unsigned int sel_trig = TRM::reg_L1Ext | TRM::reg_EnRM; // read tag from J0??
  fModule.WriteModule(TRM::mid, TRM::laddr_sel_trig,  sel_trig);

  // Start DAQ
  fModule.WriteModule(SCR::mid, SCR::laddr_counter_reset,  1);
  fModule.WriteModule(DCT::mid, DCT::laddr_gate,  1);

  static int spill_counter = 0;
  std::cout << "start scaler ..." << std::endl;
  unsigned int buf[NofData];
  // two time stamp in [ms] to normalize spill_off and clock data
  long int time_pre = 0;
  long int time_aft = 0;
  while(!user_stop){
    int spill_on_flag = 0;
    int spill_off_flag = 0;
    int clock_flag = 0;
    int trigger_type = 0; // spill_on = 1, spill_off = 10, clock = 100

    int n_word;
    while( -1 == ( n_word = Event_Cycle(sock, buf)) && !user_stop) continue;
    if(user_stop) break;
      
    // to fill out SCR block at 0xf0000000
    if(buf[0] == 0xFFFF4ca1){ // header section
      std::cout << "scaler header found" << std::endl;
      std::cout << "event size = " << std::dec << (buf[1]&0x7ff) << std::endl;
      std::cout << "event id = " << std::dec << (buf[2]&0xffff) << std::endl;
    }else{
      std::cerr << "data corrupted!!" << std::endl;
    }

    static const int n_channel = 32;
    for(int i=0; i<n_channel; ++i){
      { // U
        int ch = i;
        unsigned int val = buf[header_size + ch] & 0xfffffff;
        scaler_map[ch] = val;
        std::cout << std::left << std::setw(20) << counter_map[ch]
                  << std::right << std::setw(15) << val << "\t";
      }
      { // D
        int ch = i + n_channel;
        unsigned int val = buf[header_size + ch] & 0xfffffff;
        scaler_map[ch] = val;
        std::cout << std::left << std::setw(20) << counter_map[ch]
                  << std::right << std::setw(15) << val << "\n";
      }
    }
    struct timeval tp;
    gettimeofday(&tp, NULL);
    time_pre = time_aft;
    time_aft = tp.tv_sec * 1000 + tp.tv_usec / 1000;

    // skip the first spill to avoid data segmentation
    if(spill_counter == 0 || time_pre == 0){
      spill_counter++;
      // reset scaler data
      fModule.WriteModule(SCR::mid, SCR::laddr_counter_reset,  1);
      continue;
    }
      
    // data section
    // we need to check trigger type first: SpillStart, SpillEnd or ClockTrigger
    for(int i = 0; i<D_ch_size; i++){
      int hul_ch = i + header_size + U_ch_size;
      if((buf[hul_ch]>>28)!=0x9){
        std::cout << "Wrong board bit!! " << std::endl; 
      }else{
        // only record data registered to counter map
        if(!counter_map_D[i].empty()){
          if(counter_map_D[i].compare("SpillStart") == 0){
            std::cout << "SpillStart: " << std::dec << (buf[hul_ch]&0x0fffffff) << std::endl;
            if((buf[hul_ch]&0x0fffffff) == 1){
              spill_off_flag = 1;
              trigger_type = 10;
            }
          }else if(counter_map_D[i].compare("SpillEnd") == 0){
            std::cout << "SpillEnd: " << std::dec << (buf[hul_ch]&0x0fffffff) << std::endl;
            if((buf[hul_ch]&0x0fffffff) == 1){
              spill_on_flag = 1;
              trigger_type = 1;
            }
          }else if(counter_map_D[i].compare("ClockTrigger") == 0){
            std::cout << "ClockTrigger: " << std::dec << (buf[hul_ch]&0x0fffffff) << std::endl;
            if((buf[hul_ch]&0x0fffffff) == 1){
              clock_flag = 1;
              trigger_type = 100;
            }
          }
        } // not empty
      }// else
    }// for D_ch_size

    // check trigger type and make sure its mutually exclusive
    std::string trigger_flag;
    if((spill_on_flag + spill_off_flag + clock_flag )!= 1){
      std::cerr << "#W Wrong trigger type!! " << std::endl
                << "spill_on_flag = " << spill_on_flag << std::endl
                << "spill_off_flag = " << spill_off_flag << std::endl
                << "clock_flag = " << clock_flag << std::endl
                << "move on without recording!! " << std::endl;
      fModule.WriteModule(SCR::mid, SCR::laddr_counter_reset,  1);
      continue;
    }else{
      if(trigger_type == 1){
        std::cout << "TriggerType " << std::right << std::setw(2) 
                  << trigger_type << " spill_on data " << "\n";
        trigger_flag = "Spill On";
      }else if(trigger_type == 10){
        std::cout << "TriggerType " << std::right << std::setw(2) 
                  << trigger_type << " spill_off data " << "\n";
        trigger_flag = "Spill Off";
      }else if(trigger_type == 100){
        std::cout << "TriggerType " << std::right << std::setw(2) 
                  << trigger_type << " clock data " << "\n";
        trigger_flag = "Clock";
      }else{
        std::cout << "TriggerType " << std::right << std::setw(2) 
                  << trigger_type << " unknown trigger type!! " << "\n";
        trigger_flag = "Unknown";
      }
    }

    fModule.WriteModule(SCR::mid, SCR::laddr_counter_reset,  1);
    postgres::insert(ip, trigger_flag.c_str(), time_aft - time_pre, scaler_map);
    scaler_map.clear();
    std::cout << std::string(80, '=') << std::endl;
  }
  
  fModule.WriteModule(DCT::mid, DCT::laddr_gate,  0);
  sleep(1);
  while(-1 != Event_Cycle(sock, buf));
  close(sock);
}

// ConnectSocket ----------------------------------------------------------
int
ConnectSocket(const char* ip)
{
  struct sockaddr_in SiTCP_ADDR;
  unsigned int port = 24;

  int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
  SiTCP_ADDR.sin_family      = AF_INET;
  SiTCP_ADDR.sin_port        = htons((unsigned short int) port);
  SiTCP_ADDR.sin_addr.s_addr = inet_addr(ip);

  struct timeval tv;
  tv.tv_sec  = 3;
  tv.tv_usec = 0;
  setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (char*)&tv, sizeof(tv));

  int flag = 1;
  setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, (char*)&flag, sizeof(flag));

  if(0 > connect(sock, (struct sockaddr*)&SiTCP_ADDR, sizeof(SiTCP_ADDR))){
    std::cerr << "#E : TCP connection error" << std::endl;
    close(sock);
    return -1;
  }
  
  return sock;
}

// Event Cycle ------------------------------------------------------------
int
Event_Cycle(int sock, unsigned int* buffer)
{
  // data read ---------------------------------------------------------
  static const unsigned int sizeHeader = NofHead*sizeof(unsigned int);
  int ret = receive(sock, (char*)buffer, sizeHeader);
  if(ret < 0) return -1;

  unsigned int n_word_data  = buffer[1] & 0x3ff;
  unsigned int sizeData     = n_word_data*sizeof(unsigned int);

  if(n_word_data == 0) return NofHead;

  ret = receive(sock, (char*)(buffer + NofHead), sizeData);
  if(ret < 0) return -1;
  
  return NofHead+ n_word_data;
}

// receive ----------------------------------------------------------------
int
receive(int sock, char* data_buf, unsigned int length)
{
  unsigned int revd_size = 0;
  int tmp_ret            = 0;

  while(revd_size < length){
    tmp_ret = recv(sock, data_buf + revd_size, length -revd_size, 0);

    if(tmp_ret == 0) break;
    if(tmp_ret < 0){
      int errbuf = errno;
      perror("TCP receive");
      if(errbuf == EAGAIN){
	// this is time out
      }else{
	// something wrong
	std::cerr << "TCP error : " << errbuf << std::endl;
      }

      revd_size = tmp_ret;
      break;
    }

    revd_size += tmp_ret;
  }

  return revd_size;
}

