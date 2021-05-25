.PHONY: all clean

all:
	# Compiled versions of these binary modules are available at the url below.
	# This avoids a dependency on go and keeps the binaries out of our git repository.
	# https://ansible-ci-files.s3.amazonaws.com/test/integration/roles/test_binary_modules/
	cd library; \
	GOOS=linux   GOARCH=amd64   go build -o helloworld_linux_x86_64       helloworld.go; \
	GOOS=linux   GOARCH=ppc64le go build -o helloworld_linux_ppc64le      helloworld.go; \
	GOOS=aix     GOARCH=ppc64   go build -o helloworld_aix_chrp           helloworld.go; \
	GOOS=windows GOARCH=amd64   go build -o helloworld_win32nt_64-bit.exe helloworld.go; \
	GOOS=darwin  GOARCH=amd64   go build -o helloworld_darwin_x86_64      helloworld.go; \
	GOOS=freebsd GOARCH=amd64   go build -o helloworld_freebsd_amd64      helloworld.go

clean:
	rm -f library/helloworld_*
