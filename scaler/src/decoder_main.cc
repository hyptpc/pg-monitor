#include<iostream>
#include<fstream>
#include<string>
#include<ios>
#include"gzfilter.hh"

#include"TH1.h"
#include"TFile.h"
#include"TTree.h"
#include"TROOT.h"

static const int NofCh       = 128;
static const int NofChBlock  = 32;

unsigned int scaler[NofCh] = {0};

enum index_argv{
  i_bin, i_RunNo, size_index
};

int main(int argc, char* argv[])
{
  // File open
  std::string run_number   = argv[i_RunNo];
  std::string infile_path  = "data/run" + run_number + ".dat.gz";
  std::string outfile_path = "rootfile/run" + run_number + ".root";

  std::ifstream ifs_org(infile_path.c_str());
  if(!ifs_org.is_open()){
    std::cerr << "#E: no such file " << infile_path << std::endl;
    return -1;
  }

  h_Utility::igzfilter ifs(ifs_org);

  std::cout << "#D: Start decode, Run No. " << run_number << std::endl;

  // ROOT file create
  TFile fout(outfile_path.c_str(), "recreate");
  TTree tree("tree", "tree");
  tree.Branch("scaler",          scaler,          "scaler[128]/i");

  // decode
  static const unsigned int magic    = 0xffff4ca1;
  static const unsigned int magic_head     = 0xf;
  static const unsigned int magic_rvm      = 0xf9;
  static const unsigned int magic_block1   = 0x8;
  static const unsigned int magic_block2   = 0x9;
  static const unsigned int magic_block3   = 0xA;
  static const unsigned int magic_block4   = 0xB;

  static const int shift_data_head = 28;
  static const int mask_data_head  = 0xf;

  static const int mask_nword= 0x7ff;

  static const int mask_scaler = 0xfffffff;

  unsigned int buf[2500];
  unsigned int header1;
  unsigned int header2;
  unsigned int header3;
  int          n_of_word;

  while(!ifs.eof()){
    ifs.read((char*)&header1, sizeof(unsigned int ));
    if(header1 == magic){
      // header
      ifs.read((char*)&header2, sizeof(unsigned int ));
      ifs.read((char*)&header3, sizeof(unsigned int ));
      n_of_word = header2 & mask_nword;

      // data body
      ifs.read((char*)buf, n_of_word*sizeof(unsigned int ));
      int n_read_word = ifs.gcount()/(int)sizeof(unsigned int);
      //      std::cout << "read " << n_read_word << std::endl;
      //      std::cout << "head " << n_of_word << std::endl;
      if(n_read_word != n_of_word){
	if(!ifs.eof()){
	  // not eof
	  std::cerr << "#E: read count mis-match" << std::endl;
	}else{
	  break;
	}

      }// error

      int index       = 0;
      int ch_block[4] = {0};

      for(int i = 0; i<n_of_word; ++i){
	unsigned int data_header = (buf[i] >> shift_data_head) & mask_data_head;
	if(data_header != magic_head){
	  int offset = 0;
	  if(data_header == magic_block1) {offset= 0;  index = 0;}
	  if(data_header == magic_block2) {offset= 32; index = 1;}
	  if(data_header == magic_block3) {offset= 64; index = 2;}
	  if(data_header == magic_block4) {offset= 96; index = 3;}

	  unsigned int data_scaler = (buf[i]) & mask_scaler;
	  scaler[offset + ch_block[index]++] = data_scaler;
	}// leading data

      }// for(i)

      tree.Fill();
    }// decode one event
  }// while

  fout.Write();
  fout.Close();

  std::cout << "#D: End of decode" << std::endl;

  return 0;
}
