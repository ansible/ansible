var done = false;
while(rs.status()['myState'] != 1) {
		if (!done) {
			//print("State is not yet PRIMARY. Waiting...");
			done = true
		}
		sleep(10);
	}
