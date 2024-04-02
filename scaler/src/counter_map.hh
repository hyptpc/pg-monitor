#ifndef COUNTER_MAP_H
#define COUNTER_MAP_H

#include <cstdio>
#include <iostream>
#include <vector>

static const std::vector<std::string> counter_map =
  {
    "FT", // 0
    "TM", // 1
    "SYIM", // 2
    "BHT", // 3
    "T0", // 4
    "AC", // 5
    "T0new", // 6
    "DEF", // 7
    "Veto", // 8
    "Calori", // 9
    "BTC", // 10
    "CDH1", // 11
    "CDH2", // 12
    "CDH3", // 13
    "T98RC", // 14
    "-", // 15
    "BeamAsBHTxT0", // 16
    "BeamAsBHTxT0new", // 17
    "BeamAsT0newxDEF", // 18
    "Kaon1", // 19
    "Kaon2", // 20
    "Kaon3", // 21
    "pion1", // 22
    "pion2", // 23
    "proton", // 24
    "-", // 25
    "KaonxCDH1", // 26
    "KaonxCDH2", // 27
    "KaonxCDH3", // 28
    "KaonxCDH1xg", // 29
    "PionxCDH1", // 30
    "-", // 31
    "SpillStart", // 32
    "SpillEnd", // 33
    "BeamPrescaled", // 34
    "PionPrescaled", // 35
    "Kaon2Prescaled", // 36
    "Kaon3Prescaled", // 37
    "KaonxCDH1_trig", // 38
    "KaonxCDH2_trig", // 39
    "KaonxCDH3_trig", // 40
    "KaonxCDH1xg_trig", // 41
    "Kaonxgamma_trig", // 42
    "PionxCDH_trig", // 43
    "PionxPbF2_trig", // 44
    "ElectronxPbF2_trig", // 45
    "CDH_cosmic", // 46
    "ProtonPrescaled", // 47
    "Request", // 48
    "Accept", // 49
    "RealTime", // 50
    "DeadTime", // 51
    "Clock10kHz", // 52
    "-", // 53
    "-", // 54
    "-", // 55
    "-", // 56
    "-", // 57
    "-", // 58
    "-", // 59
    "-", // 60
    "-", // 61
    "-", // 62
    "ClockTrigger" // 63
  };

extern std::string counter_map_U[32];
extern std::string counter_map_D[32];

#endif
