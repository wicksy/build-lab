#!/usr/bin/python

import sys, json;

host_info=json.load(sys.stdin); 
dept="";

parms=host_info["host"]["parameters"]

for i in range(len(parms)):
  name=host_info["host"]["parameters"][i]["name"] 
  if name == "Department":
      dept=host_info["host"]["parameters"][i]["value"];

print host_info["host"]["uuid"], dept;
