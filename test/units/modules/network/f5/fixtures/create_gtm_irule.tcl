when LB_SELECTED {
   # Capture IP address chosen by WIP load balancing
   set wipHost [LB::server addr]
}

when LB_FAILED {
   set wipHost [LB::server addr]
}
