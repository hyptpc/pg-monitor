#include <unistd.h>
#include <iostream>
#include <string>
#include <cstring>
#include <fstream>
#include <sstream>
#include <signal.h>
#include <vector>
#include <iomanip>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <locale>

#include"counter_map.hh"

using namespace std;
static int run_flag = 1; // to control e57_scan, quit with ctrl+c
static int update_flag = 0; // to check data file update status for accumulating spill data
static int spill_flag = 1; // to control accumulated spills

const int header_size = 2; // TimeStamp and TriggerType
const int U_ch_size = 32; // upper block
const int D_ch_size = 32; // lower block

void on_catch_int(int sigid)
{
  printf("terminal interrupt accepted \n");
  run_flag = 0;
  spill_flag = 0;
}

int main(int argc, char* argv[])
{
  signal(SIGINT, on_catch_int);
  
  if(1 == argc){
    std::cout << "Usage\n";
    std::cout << "bin/sheet #run_number" << std::endl;
    return 0;
  }// usage

  std::istringstream run_ss(argv[1]); 
  int run_num;
  if (!(run_ss >> run_num)) {
    std::cerr << "Invalid number: " << argv[1] << '\n';
  } else if (!run_ss.eof()) {
    std::cerr << "Trailing characters after number: " << argv[1] << '\n';
  }
  
  char filename[256];
  std::ofstream outfile;
  // start a new file for scaned data
  sprintf(filename, "./data/sheet_%04d.txt", run_num );
  outfile.open(filename, std::ios::trunc);
  cout << "save scaler sheet as: " << filename << endl;

  int accumulated_spill = 10;
  if(3==argc) accumulated_spill = atoi(argv[2]);
  std::cout << "we will accumulate " << accumulated_spill << " spills..." << std::endl;
  static int spill_counter = 0;
  //  cout << "spill_flag = " << spill_flag << endl;
  std::ifstream infile( "./data/scaler_on.txt" );
  long int data_ele = 0;
  std::vector<long int> data_buf;
  long int data_sum[100] = {0};
  long unixtime=0;
  if ( !infile.is_open() )
    {
      cout << "infile is not open!! " << endl;
      exit( EXIT_FAILURE );
    }
  else
    {
      cout << "infile open... " << endl;
    }
  //  while ( spill_flag && run_flag )
  while ( run_flag )
    { // loop for spill accumulation
      std::string line;
      // move to the end of the data file and poll on the data file 
      // till it is flushed by bin/e57_scaler
      infile.seekg( 0, ios_base::end );
      while ( std::getline(infile, line) ) 
	{
	  update_flag = 1; // data file updated, in crement spill_counter;
	  //std::cout << line << "\n";
	  // to skip comment line
	  if( line.size() && line[0] =='#' )
	    {
	      continue;
	    }
	  std::stringstream ss( line );
	  std::cout << "read line: " << line << endl;
	  while ( ss >> data_ele ) 
	    { 
	      //cout << "data_ele: " << data_ele << endl;
	      data_buf.push_back( data_ele );
	    }
	  unixtime=data_buf[0];
	  for (int i=0; i < data_buf.size(); i++) 
	    {
	      //cout << data_buf[i] << endl;
	      data_sum[i] += data_buf[i];
	    }	  
	} // get line loop
      
      data_buf.clear(); //clear current line buffer
      // statistics achieved, quit scan
      if ( spill_counter == accumulated_spill )
	{
	  //spill_flag = 0;
	  break;
	}
      if ( update_flag )
	{
	  spill_counter++;
	  std::cout << "spill_counter = "<< spill_counter << std::endl;
	}
      // sleep(1); --> cannot use sleep() here, we may loose infile control...
      update_flag = 0;
      infile.clear();
    } // spill accumulation loop  

  char date[64];
  time_t t = unixtime;
  strftime(date, sizeof(date), "%Y/%m/%d %a %H:%M:%S", localtime(&t));
  // format accumulated scaler data and dump into sheet file  
  // data_sum[i]: TimeStamp, TriggerType, upper block (32ch), lower block (32ch)
  cout << "scaler sheet #"<< run_num 
  <<": averaged for " << accumulated_spill << " spills has been generated ..." << endl;
  outfile << "Run#"<< run_num 
  <<": averaged for " << accumulated_spill << " spills; raw data (TM normalized) " << "; last spill at "<<date<<endl;
  long int TM = 1;
  TM = data_sum[3];  // no need to be devided by accumulated spill
  if ( TM == 0 )
    TM = 1;

  // for ( int i = 0; i < 32; i++ )
  //   {
  //     if ( counter_map_U[i].empty() ) // skip undefined channel
  // 	continue;
  //     int ch = header_size + i;
  //     if ( (i+1)%2 == 0 )
  // 	{
  // 	  // double  ave = 1.0*data_sum[ch]/accumulated_spill;
  // 	  // double norm = 1.0*data_sum[ch]*norm_factor;
  // 	  long int  ave = data_sum[ch]/accumulated_spill;
  // 	  long int norm = data_sum[ch]*1000000/TM;
  // 	  outfile << std::right << std::setw(25) << counter_map_U[i];
  // 	  outfile << std::right << std::setw(12) << ave;
  // 	  outfile << "    (" ;
  // 	  outfile << std::right << std::setw(12) << norm;
  // 	  outfile << ")";
  // 	  outfile << endl;
  // 	}
  //     if ( (i+1)%2 == 1 )
  // 	{
  // 	  long int  ave = data_sum[ch]/accumulated_spill;
  // 	  long int norm = data_sum[ch]*1000000/TM;
  // 	  outfile << std::right << std::setw(20) << counter_map_U[i];
  // 	  outfile << std::right << std::setw(12) << ave;
  // 	  outfile << "    (" ;
  // 	  outfile << std::right << std::setw(12) << norm;
  // 	  outfile << ")" ;
  // 	}
  //     line_counter++
  //   }
  // for ( int i = 0; i < 32; i++ )
  //   {
  //     if ( counter_map_D[i].empty() ) // skip undefined channel
  // 	continue;
  //     int ch = header_size + U_ch_size + i;
  //     if ( (i+1)%2 == 0 )
  // 	{
  // 	  long int  ave = data_sum[ch]/accumulated_spill;
  // 	  long int norm = data_sum[ch]*1000000/TM;
  // 	  outfile << std::right << std::setw(25) << counter_map_D[i];
  // 	  outfile << std::right << std::setw(12) << ave;
  // 	  outfile << "    (" ;
  // 	  outfile << std::right << std::setw(12) << norm;
  // 	  outfile << ")" ;
  // 	  outfile << endl;
  // 	}
  //     if ( (i+1)%2 == 1 )
  // 	{
  // 	  long int  ave = data_sum[ch]/accumulated_spill;
  // 	  long int norm = data_sum[ch]*1000000/TM;	  
  // 	  outfile << std::right << std::setw(20) << counter_map_D[i];
  // 	  outfile << std::right << std::setw(12) << ave;
  // 	  outfile << "    (" ;
  // 	  outfile << std::right << std::setw(12) << norm;
  // 	  outfile << ")" ;
  // 	}
  //   }

  int line_counter = 27;

  //  std::cout.imbue(std::locale(""));
  outfile.imbue(std::locale(""));

  for ( int i = 0; i < line_counter; i++ )
    {
      if ( counter_map_U[i].empty() ) // skip undefined channel
	continue;
      int ch = header_size + i;
      long int  ave = data_sum[ch]/accumulated_spill;
      long int norm = data_sum[ch]*1000000/TM;
      outfile << std::right << std::setw(20) << counter_map_U[i];
      outfile << std::right << std::setw(12) << ave;
      outfile << "    (" ;
      outfile << std::right << std::setw(12) << norm;
      outfile << ")" ;

      int j = i + line_counter;
      if ( j > 32 )
	{
	  j = j - 32;

	  ch = header_size + U_ch_size + j;
	  ave = data_sum[ch]/accumulated_spill;
	  norm = data_sum[ch]*1000000/TM;
	  outfile << std::right << std::setw(20) << counter_map_D[j];
	  outfile << std::right << std::setw(12) << ave;
	  outfile << "    (" ;
	  outfile << std::right << std::setw(12) << norm;
	  outfile << ")";
	  outfile << endl;
	}
      else
	{
	  ch = header_size + j;
	  ave = data_sum[ch]/accumulated_spill;
	  norm = data_sum[ch]*1000000/TM;
	  outfile << std::right << std::setw(20) << counter_map_U[j];
	  outfile << std::right << std::setw(12) << ave;
	  outfile << "    (" ;
	  outfile << std::right << std::setw(12) << norm;
	  outfile << ")";
	  outfile << endl;
	}
    }

  infile.close();
  outfile.close();

  // // copy scaler sheet to web server
  char cmnd[256];
  sprintf(cmnd, "cp ./data/sheet_%04d.txt /var/www/html/e73/sheet.txt", run_num );
  printf("%s \n", cmnd);
  system(cmnd);

  return 0;
}
