var done = false;
var iterations = 0;
while(rs.status()['myState'] != 1) {
		if (!done) {
			//print("State is not yet PRIMARY. Waiting...");
			done = true
		}
		sleep(1000);
		iterations++;
		if (iterations == 100) {
			throw new Error("Exceeded iterations limit.");
		}
	}
