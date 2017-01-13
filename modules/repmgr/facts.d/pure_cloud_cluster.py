#!/usr/bin/env python2
import socket

def ip_to_int(ip):
    if type(ip) is int:
      return ip
    if type(ip) is str:
      ip_ar = ip.split(".")
      if len(ip_ar) != 4:
        raise Exception("Invalid IP: {0}. We need 4 numbers in an IP".format(ip))
      ip=0
      for i in ip_ar:
        try:
          i=int(i)
        except:
          raise Exception("IP part {0} must be numeric".format(i))
        if i<0 or i>255:
          raise Exception("IP part {0} must be from 0-255".format(i))
        ip=ip*256+i
      return ip
    raise Exception("{0} has an invalid type for an IP.".format(ip.__repr__()))

def int_to_ip(i):
    if type(i) is str:
      return i
    try:
      i = int(i)
    except:
      raise Exception("{0} is not an integer.".format(i.__repr__()))
    ip = ""
    for x in range(4):
      ip += "." + str(int(i/2**(8*(3-x)) % 256))
    return ip[1:]

def cidr_to_netmask(cidr):
    if type(cidr) is str:
      if '/' in cidr:
        cidr=cidr.split('/')[1]
    try:
      cidr=int(cidr)
    except:
      raise Exception("invalid numeric expression for network cidr {}".format(cidr))
    return (2**cidr-1) * 2** (32-cidr)

def network(ip, netmask):
    return ip_to_int(ip) & ip_to_int(netmask)

def gateway(ip, netmask):
    return (ip_to_int(ip) & ip_to_int(netmask))+1

def broadcast(ip, netmask):
    netmask=ip_to_int(netmask)
    #eerst network adress
    t = ip_to_int(ip) & ip_to_int(netmask)
    #daarna inverse van netmask erbij optellen
    t += ip_to_int(netmask) ^ (2 ** 32 - 1)
    return t

if __name__ == "__main__":
  import sys
  import ConfigParser
  import json

  try:
    config=ConfigParser.ConfigParser()
    config.readfp(open('/etc/sysconfig/pure_cloud_cluster.ini'))
  except:
    pass

  try:
    defaultprimarynetwork=config.get('pgpure_cloud_config', 'primarynetwork')
  except:
    defaultprimarynetwork=None
  try:
    defaultdns=config.get('pgpure_cloud_config', 'name')
  except:
    defaultdns=None

  import argparse
  parser = argparse.ArgumentParser(description='Read cluster setup from DNS.')
  parser.add_argument('-n', '--name', default=defaultdns, help='DNS name to read (Without domain, domain name from machine is used).')
  parser.add_argument('-l', '--primarynetwork', default=defaultprimarynetwork, help='Network segment of primary site. This helps to detect initial master.')
  args = parser.parse_args()

  if not args.name:
    print('You should set the DNS of this cluster with --name, or in inifile /etc/sysconfig/pure_cloud_cluster.ini')
    sys.exit()
  if '/' not in args.primarynetwork:
    print('Invalid --primarynetwork. \nShould be: IP/CIDR (e.a. 1.2.3.4/16). \nSet it in /etc/sysconfig/pure_cloud_cluster.ini or with --primarynetwork.')
    sys.exit()

  if not '.' in args.name:
    try:
      domain_name = socket.getfqdn().split('.',1)[1]
      dns = "{0}.{1}".format(args.name, domain_name)
    except:
      dns = args.name
  else:
    dns = args.name

  nw, cidr = args.primarynetwork.split('/')
  nw_start = gateway(nw, cidr_to_netmask(cidr)) - 1
  nw_end = broadcast(nw, cidr_to_netmask(cidr)) + 1
  #print(nw, cidr, int_to_ip(nw_start), int_to_ip(nw_end))

  try:
    IPs = socket.gethostbyname_ex(dns)
    if not IPs:
      raise Exception
  except:
    print('no IPs found by DNS {0}.'.format(dns))
    sys.exit()

  #All IP addresses that are in the primary network
  #print(ip_to_int(IPs[2][0]), nw_start, nw_end)
  primary_site = set()
  secondary_site = set()
  for IP in IPs[2]:
    IP_int = ip_to_int(IP)
    if IP_int > nw_start and IP_int < nw_end:
      primary_site.add(IP_int)
    else:
      secondary_site.add(IP_int)

  primary_site = sorted(primary_site)
  initialmaster=int_to_ip(primary_site[0])
  primary_site = [ int_to_ip(IP) for IP in primary_site ]
  secondary_site = [ int_to_ip(IP) for IP in sorted(secondary_site) ]

  facts = dict()
  facts['pure_cloud_dns'] = dns
  facts['pure_cloud_primarysite'] = primary_site
  facts['pure_cloud_secondarysite'] = secondary_site
  facts['pure_cloud_initialmaster'] = initialmaster

  print(json.dumps(facts))