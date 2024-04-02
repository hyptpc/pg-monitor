#!/usr/bin/env make

BINDIR		= ../bin
CXXFLAGS	+= -Wall -g -MMD
CXXFLAGS	+= $(shell root-config --cflags)
CXXFLAGS	+= -I/usr/pgsql-15/include
LDFLAGS		+= -lz $(shell root-config --libs)
LDFLAGS		+= -L/usr/pgsql-15/lib -lpq

SRCALL		= $(wildcard *.cc)
DEPENDS		= $(SRCALL:.cc=.d)

SRC		= $(filter-out %main.cc,$(SRCALL))
OBJ		= $(SRC:.cc=.o)

all: scaler # sheet counter_map

scaler: $(BINDIR)/scaler

$(BINDIR)/scaler: scaler_main.o $(OBJ)
	@mkdir -p $(BINDIR)
	$(CXX) -o $(BINDIR)/$@ $< $(OBJ) $(LDFLAGS)

# sheet: sheet_main.o $(OBJ)
# 	$(CXX) -o $(BINDIR)/$@ $< $(OBJ) $(LDFLAGS)

# counter_map: counter_map_main.o $(OBJ)
# 	$(CXX) -o $(BINDIR)/$@ $< $(OBJ) $(LDFLAGS)

clean:
	$(RM) $(BINDIR)/* *.o *.d *~

-include $(DEPENDS)
