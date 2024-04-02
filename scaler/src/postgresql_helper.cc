// -*- C++ -*-

#include "postgresql_helper.hh"

#include <cstdlib>
#include <iostream>
#include <sstream>
#include <libpq-fe.h>

#include "counter_map.hh"

namespace postgres
{
bool
insert(const char* ip_address, const char* trigger_flag, double duration,
       const std::map<int, unsigned long long>& scaler_map)
{
  char pghost[] = "192.168.1.248";
  char pgport[] = "5432";
  char dbName[] = "e73";
  char login[] = "postgres";
  char pwd[] = "pg";
  
  PGconn* con = PQsetdbLogin(pghost, pgport, nullptr, nullptr,
                             dbName, login, pwd);
  if(PQstatus(con) == CONNECTION_BAD){
    fprintf(stderr, "Connection to database '%s' failed.\n", dbName);
    fprintf(stderr, "%s", PQerrorMessage(con));
    std::exit(1);
  }

  std::stringstream sql;
  sql << "INSERT INTO scaler (ip_address, timestamp, trigger, channel, name, value, duration) VALUES";
  for(int i=0, n=scaler_map.size(); i<n; ++i){
    std::string name = counter_map[i];
    sql << " ('" << ip_address << "', " << "NOW(), '" << trigger_flag << "', "
        << i << ", '" << name << "', " << scaler_map.at(i) << ", " << duration << ")";
    if(i != n-1) sql << ", ";
  }

  PGresult* res = PQexec(con, sql.str().c_str());
  if(PQresultStatus(res) != PGRES_COMMAND_OK){
    fprintf(stderr,"%s",PQerrorMessage(con));
    std::exit(1);
  }

  PQclear(res);
  PQfinish(con);
  return true;
}
}
