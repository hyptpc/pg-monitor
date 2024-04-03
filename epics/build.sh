#!/bin/sh

cd $(dirname $0)

if [ -d base-7.0 ] && [ -s base ]; then
    cd base
    #git pull --recurse-submodules
    cd ..
else
    rm -rf base-7.0 base
    git clone --recursive -b 7.0 https://git.launchpad.net/epics-base base-7.0
    ln -s base-7.0 base
fi

# target=epicsApp/configure/RELEASE
# sed -i -e s:^EPICS_BASE.*:EPICS_BASE=$PWD/base:g $target
cd base
target=configure/CONFIG_SITE_ENV
# cp $target configure/CONFIG_SITE_ENV.$(date +%Y%m%d%H%M%S)
sed -i -e 's/^#EPICS_TZ = "JST-9"/EPICS_TZ = "JST-9"/g' $target
sed -i -e 's:^EPICS_TZ = "CST6CDT,M3.2.0/2,M11.1.0/2":#EPICS_TZ = "CST6CDT,M3.2.0/2,M11.1.0/2":g' $target
target=modules/database/src/ioc/db/menuScan.dbd.pod
grep 20_second $target >/dev/null || \
    sed -i -e 's/fastest/fastest\n        choice(menuScan20_second,"20 second")/g' $target

make clean uninstall
make -j$(cat /proc/cpuinfo|grep processor|wc -l)
