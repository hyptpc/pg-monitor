#include <iostream>
#include <cstdio>
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

#include "counter_map.hh"

const int U_ch_size = 32;
const int D_ch_size = 32;

int main(int argc, char* argv[])
{
  
  // to generate counter map for rrd tools
  // only call this function if counter map is modified
  // genertate scaler.list for rrd tools

  char filename[256];
  sprintf(filename, "/home/oper/scaler/e73/data/scaler.list");
  std::ofstream ofs_map(filename, std::ofstream::out);
  if ( !ofs_map.is_open() ) 
    {
      std::cout << filename << " is not open!!" << std::endl;
      return -1;
    }
  //  ofs_map << "TimeStamp" << " "; // keep this empty for rrd format
  ofs_map << "TriggerType" << " ";
  for (int i = 0; i < U_ch_size; i++ )
    {
      if ( !counter_map_U[i].empty() )
	{
	  std::cout << counter_map_U[i] << std::endl;
	  ofs_map << counter_map_U[i] << " ";
	}
      else
	{
	  // keep position with dummy title
	  std::cout << "tmp_" << i+2 << std::endl;
	  ofs_map << "tmp_"<< i+2 << " ";
	}
    }
  for (int i = 0; i < D_ch_size; i++ )
    {
      if ( !counter_map_D[i].empty() )
	{
	  std::cout << counter_map_D[i] << std::endl;
	  ofs_map << counter_map_D[i] << " ";
	}
      else
	{
	  // keep position with dummy title
	  std::cout << "tmp_" << i+34 << std::endl;
	  ofs_map << "tmp_"<< i+34 << " ";
	}
    }
  ofs_map << "\n";
  // additional 0 for TimeStamp and TriggerType
  //  ofs_map << "0" << " ";  // keep this empty for rrd format
  ofs_map << "0" << " ";
  for (int i = 0; i < U_ch_size; i++ )
    {
      ofs_map << "0" << " ";
    }
  for (int i = 0; i < D_ch_size; i++ )
    {
      ofs_map << "0" << " ";
    }
  ofs_map << "\n";
  // additional 1000000000 for TimeStamp and TriggerType
  //  ofs_map << "1000000000" << " ";  // keep this empty for rrd format
  ofs_map << "1000000000" << " ";
  for (int i = 0; i < U_ch_size; i++ )
    {
      ofs_map << "1000000000" << " ";
    }
  for (int i = 0; i < D_ch_size; i++ )
    {
      ofs_map << "1000000000" << " ";
    }
  ofs_map << "\n";
  ofs_map.close();

  return 0;
}// main
