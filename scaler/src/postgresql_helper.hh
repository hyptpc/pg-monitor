// -*- C++ -*-

#ifndef POSTGRESQL_HELPER_HH
#define POSTGRESQL_HELPER_HH

#include <map>

namespace postgres
{
bool insert(const char* ip_address, const char* spill_flag, double duration,
            const std::map<int, unsigned long long>& scaler_map);
}

#endif
