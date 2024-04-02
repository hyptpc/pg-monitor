#include <iostream>
#include <cstdio>

#include"counter_map.hh"

std::string counter_map_U[32] = 
  {
    "FT",  "TM", "SYIM", //2
    "BHT", "T0", "AC", "T0new", "DEF", //7
    "Veto","Calori","BTC",//10
    "CDH1", "CDH2", "CDH3",//13
    "T98RC", "tmp16", //15
    "BeamAsBHTxT0", "BeamAsBHTxT0new", "BeamAsT0newxDEF",
    "Kaon1", "Kaon2", "Kaon3", 
    "pion1", "pion2", //23
    "proton", "tmp26", //25
    "KaonxCDH1", "KaonxCDH2","KaonxCDH3","KaonxCDH1xg",
    "PionxCDH1","tmp31"
  };
// define counter map for lower block
std::string counter_map_D[32] =
  {
    "SpillStart", // for spill off data
    "SpillEnd", // for spill on data
    "BeamPrescaled",
    "PionPrescaled",//3
    "Kaon2Prescaled",
    "Kaon3Prescaled",
    "KaonxCDH1_trig",
    "KaonxCDH2_trig",//7
    "KaonxCDH3_trig",
    "KaonxCDH1xg_trig",
    "Kaonxgamma_trig",
    "PionxCDH_trig",//11
    "PionxPbF2_trig",
    "ElectronxPbF2_trig",
    "CDH_cosmic",
    "ProtonPrescaled",//15
    "Request", "Accept", //17
    "RealTime","DeadTime",//19
    "Clock10kHz",
    "tmp54","tmp55","tmp56",
    "tmp57","tmp58","tmp59","tmp60",
    "tmp61","tmp62","tmp63",
    "ClockTrigger"// for spill off
  };
