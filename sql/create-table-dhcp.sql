CREATE TABLE dhcp
(timestamp  TIMESTAMP WITH TIME ZONE,
 ip_address  TEXT,
 host_name   TEXT,
 start_time  TIMESTAMP WITH TIME ZONE,
 end_time    TIMESTAMP WITH TIME ZONE,
 state       TEXT,
 mac_address TEXT,
 CONSTRAINT dhcp_hosts_pkey PRIMARY KEY (ip_address));
